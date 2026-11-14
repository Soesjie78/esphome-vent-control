#!/usr/bin/env python3
"""Small grid-based A* router for this 2-layer board (KiCad python).

* 0.1 mm grid, 8-directional moves (0/45/90 degree tracks), vias between layers.
* Clearances are enforced by dilating all foreign copper with
  (clearance + track_width/2 + safety margin); KiCad's DRC checks the result.
* Signals prefer F.Cu; B.Cu is kept as free as possible for the GND pour.
* GND is not routed as a tree: every SMD GND pad gets a short stub to a via
  into the B.Cu ground pour (finish_pcb.py adds the pours on both layers).

Usage: /usr/bin/python3 route.py
"""
import heapq
import math
import os
import sys
import numpy as np
import pcbnew
import design
from gen_pcb import OX, OY, W, H, ANT_Y, OUT

RES = 0.1                    # grid (mm)
CLEAR = 0.2                  # copper clearance (mm)
MARGIN = 0.08                # safety margin for rasterisation (mm)
EDGE = 0.3                   # copper-to-edge clearance (mm)
VIA_D, VIA_DRILL = 0.6, 0.3
WIDTH = {n: 0.4 for n in design.POWER_NETS}
SIG_W = 0.25
FINE = {"USB_DP": 0.2, "USB_DN": 0.2, "CC1": 0.2, "CC2": 0.2}   # fine-pitch USB-C pads
WIDTH.update(FINE)
WIDTH["VBUS"] = 0.3
HOLE_CLEAR = 0.25
LAYER_COST = (1.0, 2.5)      # F.Cu, B.Cu
VIA_COST = 25.0

NX, NY = int(round(W / RES)), int(round(H / RES))
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)
xs = (np.arange(NX) + 0.5) * RES
ys = (np.arange(NY) + 0.5) * RES
GX, GY = np.meshgrid(xs, ys)


def mm(v):
    return pcbnew.FromMM(float(v))


def cell_xy(i, j):
    return (i + 0.5) * RES, (j + 0.5) * RES


def disk(r_cells):
    r = int(math.ceil(r_cells))
    return [(dx, dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if dx * dx + dy * dy <= r_cells * r_cells]


def dilate(mask, r_mm):
    out = mask.copy()
    for dx, dy in disk(r_mm / RES):
        if dx == 0 and dy == 0:
            continue
        src = mask[max(0, -dy):NY - max(0, dy), max(0, -dx):NX - max(0, dx)]
        out[max(0, dy):NY - max(0, -dy), max(0, dx):NX - max(0, -dx)] |= src
    return out


class Router:
    def __init__(self, board):
        self.board = board
        self.owner = np.full((2, NY, NX), -1, np.int32)   # -1 free, -2 forbidden, >=0 net code
        self.holes = np.zeros((NY, NX), bool)              # drilled holes (for via hole-to-hole)
        self.netcode = {n: board.FindNet(n).GetNetCode() for n in design.NETS}
        self.pads = {}                                     # net -> list of (pad, cells set per layer)
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                self.raster_pad(pad)
        # keep the inside of the module pad ring free (GND island under the module)
        u1 = board.FindFootprintByReference("U1").GetPosition()
        ux, uy = pcbnew.ToMM(u1.x) - OX, pcbnew.ToMM(u1.y) - OY
        inner = (np.abs(GX - ux) < 5.3) & (np.abs(GY - uy) < 4.3) & (self.owner[0] == -1)
        self.owner[0][inner] = -2
        # distance-to-edge and keep-out masks (centre-line restrictions)
        self.edge_dist = np.minimum.reduce([GX, W - GX, GY, H - GY])

    # -------------------------------------------------------------- raster
    def raster_pad(self, pad):
        bb = pad.GetBoundingBox()
        x1, y1 = pcbnew.ToMM(bb.GetX()) - OX, pcbnew.ToMM(bb.GetY()) - OY
        x2, y2 = x1 + pcbnew.ToMM(bb.GetWidth()), y1 + pcbnew.ToMM(bb.GetHeight())
        i1, i2 = max(0, int(x1 / RES) - 1), min(NX, int(x2 / RES) + 2)
        j1, j2 = max(0, int(y1 / RES) - 1), min(NY, int(y2 / RES) + 2)
        npth = pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
        code = -2 if npth else pad.GetNetCode()
        cells = []
        for j in range(j1, j2):
            for i in range(i1, i2):
                x, y = cell_xy(i, j)
                if pad.HitTest(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))):
                    cells.append((i, j))
        layers = [li for li, L in enumerate(LAYERS) if npth or pad.IsOnLayer(L)]
        if pad.HasHole():
            c = pad.GetPosition()
            hx, hy = pcbnew.ToMM(c.x) - OX, pcbnew.ToMM(c.y) - OY
            hr = pcbnew.ToMM(max(pad.GetDrillSize().x, pad.GetDrillSize().y)) / 2
            hm = np.hypot(GX - hx, GY - hy) <= hr
            self.holes |= hm
            if npth:   # NPTH: copper must keep the (larger) hole clearance
                hm2 = np.hypot(GX - hx, GY - hy) <= hr + (HOLE_CLEAR - CLEAR) + 0.05
                self.owner[:, hm2] = -2
        for li in layers:
            for i, j in cells:
                self.owner[li, j, i] = code
        if not npth and pad.GetNetname() in self.netcode:
            self.pads.setdefault(pad.GetNetname(), []).append((pad, layers, cells))

    def raster_segment(self, li, a, b, w, code):
        (ax, ay), (bx, by) = a, b
        r = w / 2
        i1, i2 = max(0, int((min(ax, bx) - r) / RES) - 1), min(NX, int((max(ax, bx) + r) / RES) + 2)
        j1, j2 = max(0, int((min(ay, by) - r) / RES) - 1), min(NY, int((max(ay, by) + r) / RES) + 2)
        px, py = GX[j1:j2, i1:i2], GY[j1:j2, i1:i2]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0, 1) if L2 > 0 else 0
        d = np.hypot(px - (ax + t * dx), py - (ay + t * dy))
        sub = self.owner[li, j1:j2, i1:i2]
        sub[(d <= r) & (sub == -1)] = code

    # -------------------------------------------------------------- masks
    def blocked(self, code, w, margin=MARGIN):
        r = CLEAR + w / 2 + margin
        out = []
        for li in range(2):
            o = self.owner[li]
            foreign = ((o >= 0) & (o != code)) | (o == -2)
            b = dilate(foreign, r)
            b |= self.edge_dist < EDGE + w / 2 + MARGIN
            b |= GY < ANT_Y + w / 2 + MARGIN
            out.append(b)
        rv = CLEAR + VIA_D / 2 + MARGIN
        via = np.zeros((NY, NX), bool)
        for li in range(2):
            o = self.owner[li]
            via |= dilate(((o >= 0) & (o != code)) | (o == -2), rv)
        via |= dilate(self.holes, VIA_DRILL / 2 + HOLE_CLEAR + MARGIN)
        via |= self.edge_dist < EDGE + VIA_D / 2 + MARGIN
        via |= GY < ANT_Y + VIA_D / 2 + MARGIN
        return out, via

    # -------------------------------------------------------------- A*
    def astar(self, sources, targets, blk, via_blk, target_any_via=False, max_exp=3_000_000):
        """sources: iterable of (l,i,j); targets: set of (l,i,j). Returns node path."""
        INF = 1e18
        N = 2 * NY * NX
        g = np.full(N, INF)
        parent = np.full(N, -1, np.int64)
        tl = np.array(sorted(targets)) if targets else None
        tset = {(l * NY + j) * NX + i for l, i, j in targets}

        def h(i, j):
            if tl is None:
                return 0.0
            dx = np.abs(tl[:, 1] - i)
            dy = np.abs(tl[:, 2] - j)
            return float(np.min(np.maximum(dx, dy) + 0.4142 * np.minimum(dx, dy)))

        # heuristic on a coarse level: cache per cell lazily
        hcache = {}
        pq = []
        for l, i, j in sources:
            if blk[l][j, i]:
                continue
            n = (l * NY + j) * NX + i
            g[n] = 0
            hv = hcache.setdefault((i, j), h(i, j))
            heapq.heappush(pq, (hv, 0.0, n))
        steps = ((1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
                 (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142))
        exp = 0
        while pq:
            f, gc, n = heapq.heappop(pq)
            if gc > g[n]:
                continue
            l, rem = divmod(n, NY * NX)
            j, i = divmod(rem, NX)
            if n in tset or (target_any_via and l == 1):
                path = []
                while n != -1:
                    path.append(n)
                    n = parent[n]
                return [(int(p // (NY * NX)), int(p % NX), int((p % (NY * NX)) // NX)) for p in reversed(path)]
            exp += 1
            if exp > max_exp:
                return None
            lc = LAYER_COST[l]
            for dx, dy, c in steps:
                ii, jj = i + dx, j + dy
                if not (0 <= ii < NX and 0 <= jj < NY) or blk[l][jj, ii]:
                    continue
                if dx and dy and (blk[l][j, ii] or blk[l][jj, i]):
                    continue
                m = (l * NY + jj) * NX + ii
                ng = gc + c * lc
                if ng < g[m]:
                    g[m] = ng
                    parent[m] = n
                    hv = hcache.get((ii, jj))
                    if hv is None:
                        hv = hcache[(ii, jj)] = h(ii, jj)
                    heapq.heappush(pq, (ng + hv, ng, m))
            if not via_blk[j, i]:
                ol = 1 - l
                if not blk[ol][j, i]:
                    m = (ol * NY + j) * NX + i
                    ng = gc + VIA_COST
                    if ng < g[m]:
                        g[m] = ng
                        parent[m] = n
                        heapq.heappush(pq, (ng + hcache.get((i, j), 0), ng, m))
        return None

    # -------------------------------------------------------------- commit
    def commit(self, net, path, w, out):
        code = self.netcode[net]
        segs, vias = [], []
        start = path[0]
        prev = path[0]
        pdir = None
        for node in path[1:]:
            if node[0] != prev[0]:
                if prev != start:
                    segs.append((prev[0], start, prev))
                vias.append(prev)
                start = node
                pdir = None
            else:
                d = (node[1] - prev[1], node[2] - prev[2])
                if pdir is not None and d != pdir:
                    segs.append((prev[0], start, prev))
                    start = prev
                pdir = d
            prev = node
        if prev != start:
            segs.append((prev[0], start, prev))
        netinfo = self.board.FindNet(net)
        for l, a, b in segs:
            pa, pb = cell_xy(a[1], a[2]), cell_xy(b[1], b[2])
            t = pcbnew.PCB_TRACK(self.board)
            t.SetStart(pcbnew.VECTOR2I(mm(OX + pa[0]), mm(OY + pa[1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(OX + pb[0]), mm(OY + pb[1])))
            t.SetWidth(mm(w))
            t.SetLayer(LAYERS[l])
            t.SetNet(netinfo)
            self.board.Add(t)
            self.raster_segment(l, pa, pb, w, code)
            out.append(t)
        for v in vias:
            self.add_via(net, cell_xy(v[1], v[2]))
        return [n for n in path]

    def add_via(self, net, p):
        code = self.netcode[net]
        via = pcbnew.PCB_VIA(self.board)
        via.SetPosition(pcbnew.VECTOR2I(mm(OX + p[0]), mm(OY + p[1])))
        via.SetWidth(mm(VIA_D))
        via.SetDrill(mm(VIA_DRILL))
        via.SetNet(self.board.FindNet(net))
        self.board.Add(via)
        for li in range(2):
            self.raster_segment(li, p, p, VIA_D, code)
        self.holes |= np.hypot(GX - p[0], GY - p[1]) <= VIA_DRILL / 2

    # -------------------------------------------------------------- nets
    def route_net(self, net):
        w = WIDTH.get(net, SIG_W)
        code = self.netcode[net]
        margin = 0.03 if net in FINE else MARGIN
        pads = self.pads[net]
        groups = [{(l, i, j) for l in layers for i, j in cells} for pad, layers, cells in pads]
        own = set().union(*groups)

        def masks():
            b, v = self.blocked(code, w, margin)
            for l, i, j in own:
                b[l][j, i] = False
            return b, v
        blk, via_blk = masks()
        tree = set(groups[0])
        remaining = groups[1:]
        tracks = []
        while remaining:
            targets = set().union(*remaining)
            path = self.astar(tree, targets, blk, via_blk)
            if path is None:
                return False, tracks
            self.commit(net, path, w, tracks)
            end = path[-1]
            hit = [g for g in remaining if end in g][0]
            remaining.remove(hit)
            tree |= hit
            tree |= set(path)
            blk, via_blk = masks()
        return True, tracks

    def ground_stubs(self):
        """Connect each F.Cu-only GND pad to the B.Cu pour with a via, unless it is a
        module pad (those join the pour inside the module ring / EP vias)."""
        net = "GND"
        code = self.netcode[net]
        w = 0.4
        ok = True
        for pad, layers, cells in self.pads[net]:
            if len(layers) == 2:
                continue
            ref = pad.GetParent().GetReference()
            if ref == "U1":
                continue
            blk, via_blk = self.blocked(code, w)
            src = {(0, i, j) for i, j in cells}
            path = self.astar(src, set(), blk, via_blk, target_any_via=True, max_exp=400_000)
            if path is None:
                print("  GND stub failed for", ref, pad.GetNumber())
                ok = False
                continue
            self.commit(net, path, w, [])
        return ok

    def module_ep_vias(self):
        fp = self.board.FindFootprintByReference("U1")
        c = fp.GetPosition()
        cx, cy = pcbnew.ToMM(c.x) - OX, pcbnew.ToMM(c.y) - OY
        for dx in (-0.9875, 0.9875):
            for dy in (-0.9875, 0.9875):
                self.add_via("GND", (cx + dx, cy + dy))


def attempt(order):
    """Route on a freshly generated board. Returns (board, failed_nets, gnd_ok)."""
    import gen_pcb
    board = gen_pcb.build()
    r = Router(board)
    r.module_ep_vias()
    failed = []
    for n in order:
        ok, _ = r.route_net(n)
        if not ok:
            failed.append(n)
    gok = r.ground_stubs() if not failed else False
    return board, failed, gok


def initial_order():
    import gen_pcb
    pos = {}
    for ref, (x, y, _r) in gen_pcb.PLACE.items():
        pos[ref] = (x, y)

    def span(n):
        pts = [pos[p.split(".")[0]] for p in design.NETS[n]]
        xs_, ys_ = zip(*pts)
        return (max(xs_) - min(xs_)) + (max(ys_) - min(ys_))
    first = ["VBUS", "USB_DP", "USB_DN"]
    nets = [n for n in design.NETS if n != "GND"]
    return first + sorted([n for n in nets if n not in first], key=span)


def main(max_tries=12):
    order = initial_order()
    for k in range(max_tries):
        board, failed, gok = attempt(order)
        print(f"attempt {k + 1}: failed={failed} gnd_ok={gok}", flush=True)
        if not failed and gok:
            board.Save(OUT)
            print("order:", order)
            return True
        # rip-up & retry: failed nets move to the front
        order = failed + [n for n in order if n not in failed]
    return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)

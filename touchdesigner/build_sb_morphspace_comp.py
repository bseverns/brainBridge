"""SB MorphSpace COMP builder for TouchDesigner.

Run this *inside TouchDesigner* (Textport), e.g.:

    run('/ABS/PATH/TO/touchdesigner/build_sb_morphspace_comp.py')

It creates `/project1/sb_morphspace` with:
  - `oscin1` (listens on port 9001)
  - `OUT` (null)

This is intentionally minimal; treat it as a seed you can mutate.
"""

# TouchDesigner injects these names:
# - op, baseCOMP, oscinCHOP, nullCHOP, ...

def _setpar(o, name, value):
    try:
        p = getattr(o.par, name)
    except Exception:
        return False
    try:
        p.val = value
        return True
    except Exception:
        try:
            p = value
            return True
        except Exception:
            return False


def build(parent=None, port=9001):
    if parent is None:
        parent = op('/project1')

    # Remove old copy if present
    existing = parent.op('sb_morphspace')
    if existing is not None:
        try:
            existing.destroy()
        except Exception:
            pass

    c = parent.create(baseCOMP, 'sb_morphspace')
    c.nodeX, c.nodeY = 0, 0

    oscin = c.create(oscinCHOP, 'oscin1')
    oscin.nodeX, oscin.nodeY = -240, 0

    # Parameter names differ slightly across TD versions; try common ones.
    for cand in ('port', 'localport', 'port1'):
        _setpar(oscin, cand, port)

    out = c.create(nullCHOP, 'OUT')
    out.nodeX, out.nodeY = 0, 0

    # Wire: oscin -> out
    try:
        out.inputConnectors[0].connect(oscin)
    except Exception:
        pass

    try:
        c.layoutChildren()
    except Exception:
        pass

    return c


# If executed via `run()`, build immediately.
try:
    build()
    print('[sb] created /project1/sb_morphspace (osc in port 9001)')
except Exception as e:
    print('[sb] build failed:', e)

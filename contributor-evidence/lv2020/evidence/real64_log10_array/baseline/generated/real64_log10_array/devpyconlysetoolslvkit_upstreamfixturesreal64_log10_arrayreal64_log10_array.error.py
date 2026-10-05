# ERROR: Primitive resolution needed for 1210 (Logarithm Base 10).
  In VI: real64_log10_array.vi
  Full connector pane (every terminal the heap serialized — wired
  AND unwired — with its declared type; identify by this whole
  signature, not just the wired ones):
    - index=0 direction=output type=Array wired
    - index=1 direction=input type=Array wired

  Fix: add primitive 1210 to .lvkit/primitives.json (project-local) or data/primitives.json (cleanroom upstream)
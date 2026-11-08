#set page(width: auto, height: auto, margin: 4pt, fill: none)

#let py-grad = gradient.linear(
  (rgb("#38bdf8"), 0%),
  (rgb("#0ea5e9"), 45%),
  (rgb("#0284c7"), 85%),
  (rgb("#0369a1"), 100%),
)

#let thon-grad = gradient.linear(
  (rgb("#fde047"), 0%),
  (rgb("#facc15"), 35%),
  (rgb("#fbbf24"), 70%),
  (rgb("#f59e0b"), 100%),
)

#let spec = (
  font: "Cinzel",
  weight: "bold",
  tracking: 2.5pt,
  top-edge: "bounds",
  bottom-edge: "bounds",
)

#let word(s1, s2) = [#text(..s1)[PY]#h(5pt)#text(..s2)[THON]]

#context {
  let target-h = 50.91pt
  let probe = measure(text(..spec, size: 100pt, word((:), (:))))
  let sz = 100pt * (target-h / probe.height)
  let shadow-style = (
    fill: rgb("#0f172a").transparentize(80%),
    stroke: (paint: rgb("#0f172a").transparentize(80%), thickness: 1.2pt, join: "round"),
  )
  let py-rim = (
    fill: rgb("#080c14"),
    stroke: (paint: rgb("#0369a1").transparentize(35%), thickness: 1.0pt, join: "round"),
  )
  let thon-rim = (
    fill: rgb("#080c14"),
    stroke: (paint: rgb("#b45309").transparentize(30%), thickness: 1.1pt, join: "round"),
  )
  grid(
    columns: (auto, auto),
    gutter: 16pt,
    align: horizon,
    image("python-emblem.svg", width: 56pt, height: 56pt),
    box[
      #set text(..spec, size: sz)
      #place(top + left, dx: 0pt, dy: 0.6pt, word(shadow-style, shadow-style))
      #place(top + left, word(py-rim, thon-rim))
      #word((fill: py-grad), (fill: thon-grad))
    ],
  )
}

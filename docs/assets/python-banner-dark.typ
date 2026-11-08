#set page(width: auto, height: auto, margin: 4pt, fill: none)

#let py-grad = gradient.linear(
  (rgb("#ffffff"), 0%),
  (rgb("#bae6fd"), 35%),
  (rgb("#38bdf8"), 100%),
  angle: 18deg,
)

#let thon-grad = gradient.linear(
  (rgb("#fef9c3"), 0%),
  (rgb("#fde047"), 45%),
  (rgb("#ffc331"), 100%),
  angle: 18deg,
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
    fill: rgb("#020408").transparentize(50%),
    stroke: (paint: rgb("#020408").transparentize(50%), thickness: 3.2pt, join: "round"),
  )
  let border-style = (
    fill: rgb("#020408"),
    stroke: (paint: rgb("#020408"), thickness: 2.2pt, join: "round"),
  )
  grid(
    columns: (auto, auto),
    gutter: 16pt,
    align: horizon,
    image("python-emblem.svg", width: 56pt, height: 56pt),
    box[
      #set text(..spec, size: sz)
      #place(top + left, dx: 0pt, dy: 0.85pt, word(shadow-style, shadow-style))
      #place(top + left, word(border-style, border-style))
      #word((fill: py-grad), (fill: thon-grad))
    ],
  )
}

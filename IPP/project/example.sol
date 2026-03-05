class Model : Object {
    init [|
        "Změněno na 'name', aby nebyla kolize s metodou 'jmeno'"
        _ := (self name: 'Puvodni').
        _ := (self hodnota: 100).
    ]

    jmeno [|
        _ := 'Metoda jmeno'.
    ]
}

class Main : Object {
    run [|
        _ := ('--- TEST START ---\n') print.

        m1 := (Model new).
        _ := (m1 init).

        m2 := (Model from: m1).

        _ := ('Metoda m2 jmeno: ') print.
        _ := (m2 jmeno) print.
        _ := ('\n') print.

        _ := ('Atribut m2 name: ') print.
        _ := (m2 name) print.
        _ := ('\n') print.

        _ := ('Atribut m2 hodnota: ') print.
        _ := ((m2 hodnota) asString) print.
        _ := ('\n') print.

        "startsWith:endsBefore: test"
        s := 'VUTBRNO'.
        sub := (s startsWith: 1 endsBefore: 4).
        _ := ('Substring (VUT): ') print.
        _ := (sub print).
        _ := ('\n') print.

        _ := ('--- TEST END ---\n') print.
    ]
}
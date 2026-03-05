class Parent : Object {
    init [| _ := self secret: 'ParentSecret'. ]
    getSecret [| _ := self secret. ]
    whoAmI [| _ := 'I am Parent'. ]
}

class Child : Parent {
    init [|
        _ := super init.
        _ := self secret: 'ChildSecret'.
    ]
    whoAmI [| _ := 'I am Child'. ]
    testSuper [|
        _ := 'Child says: ' print.
        _ := (self whoAmI) print.
        _ := '\nParent says: ' print.
        _ := (super whoAmI) print.
    ]
    makeClosure: [ :val |
        _ := [ :extra |
            _ := ((val concatenateWith: ' ') concatenateWith: extra).
        ].
    ]
}

class Main : Object {
    run [|
        _ := '--- TEST 1 ---\n' print.
        c := Child new.
        _ := c init.
        _ := c testSuper.
        _ := '\n' print.

        _ := '--- TEST 2 ---\n' print.
        block := c makeClosure: 'Hello'.
        result := block value: 'World'.
        _ := 'Closure result: ' print.
        _ := result print.
        _ := '\n' print.

        _ := '--- TEST 3 ---\n' print.
        _ := 'nil identicalTo: nil: ' print.
        isSame := (nil identicalTo: nil).
        _ := (isSame asString) print.
        _ := '\n' print.
    ]
}
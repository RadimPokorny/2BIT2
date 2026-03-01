class Main : Object {
  run [ |
    "Vytvoření atributu 'cislo' - výsledek přiřadíme do '_'"
    _ := self cislo: 20.

    "Přiřazení do lokální proměnné 'vysl' - ta vznikne tímto řádkem"
    vysl := (self cislo) plus: 6.

    "Výpis - opět musí být součástí přiřazení"
    _ := 'Vysledek je: ' print.
    _ := (vysl asString) print.
    _ := '\n' print.
  ]
}
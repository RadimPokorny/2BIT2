# Yup I could have learned more

SELECT P.zkratkaP, P.nazev FROM Predmet P
    LEFT JOIN Rezervace R ON R.zkratkaP = P.zkratkaP
    WHERE R.den IN ("čtvrtek", "pátek")

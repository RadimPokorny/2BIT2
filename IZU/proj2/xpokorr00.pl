% Zadani c. 31:
% Napiste program resici ukol dany predikatem u31(LIN,VOUT), kde LIN je vstupni 
% ciselny seznam s nejmene jednim prvkem a VOUT je promenna, ve ktere se vraci 
% index prvniho vyskytu maximalniho cisla v seznamu LIN (indexovani zacina 
% jednickou). 

% Testovaci predikaty:                                  	% LOUT 
u31_1:- u31([5,3,-18,2,-9,-13,17,4],VOUT),write(VOUT).		% 7
u31_2:- u31([5,3.1,17,2,-9.4,-13,17,4], VOUT),write(VOUT).	% 3
u31_3:- u31([5,3.3],VOUT),write(VOUT).				% 1
u31_r:- write('Zadej LIN: '),read(LIN),
	u31(LIN,VOUT),write(VOUT).

% Reseni:
u31(LIN, VOUT) :-
    u31_max(LIN, MAX),
    u31_index(LIN, MAX, 1, VOUT).
u31_max([H], H).
u31_max([H|T], MAX) :-
    u31_max(T, MAX_TAIL),
    ( H >= MAX_TAIL ->
        MAX = H
    ;
        MAX = MAX_TAIL
    ).
u31_index([H|_], MAX, INDEX, INDEX) :-
    H =:= MAX.
u31_index([H|T], MAX, INDEX, INDEX_OUT) :-
    H =\= MAX,
    INDEX1 is INDEX + 1,
    u31_index(T, MAX, INDEX1, INDEX_OUT).


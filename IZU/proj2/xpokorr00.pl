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
u31(LIN,VOUT):-

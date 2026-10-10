function y=noiseWatt(B,NF)
assert(B>0); y=simkit.dbmToWatt(-174+10*log10(B)+NF);
end

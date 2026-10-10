function y=wattToDbm(x)
assert(all(x(:)>0)); y=10*log10(x)+30;
end

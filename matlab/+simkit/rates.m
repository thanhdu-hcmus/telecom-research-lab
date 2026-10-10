function y=rates(x)
assert(all(x(:)>=0)); y=log2(1+x);
end

function y=pathGain(d,alpha,d0,g0)
assert(all(d(:)>=d0)&&alpha>0&&g0>0); y=g0*(d/d0).^(-alpha);
end

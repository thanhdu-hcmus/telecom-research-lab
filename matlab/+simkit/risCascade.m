function y=risCascade(g,h)
z=g.*h; y=sum(z.*exp(-1i*angle(z)),2);
end

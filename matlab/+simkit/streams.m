function s=streams(seed)
s.channel=RandStream('mrg32k3a','Seed',seed); s.channel.Substream=1;
s.noise=RandStream('mrg32k3a','Seed',seed); s.noise.Substream=2;
s.initialization=RandStream('mrg32k3a','Seed',seed); s.initialization.Substream=3;
end

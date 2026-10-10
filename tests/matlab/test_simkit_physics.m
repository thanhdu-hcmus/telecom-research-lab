function tests = test_simkit_physics
% Standard matlab.unittest coverage of the framework's established physics.
tests = functiontests(localfunctions);
end

function testUnitsAndNoise(testCase)
verifyEqual(testCase, simkit.dbmToWatt(30), 1, 'AbsTol', 1e-12);
verifyEqual(testCase, simkit.wattToDbm(.001), 0, 'AbsTol', 1e-12);
verifyEqual(testCase, simkit.noiseWatt(1,0), simkit.dbmToWatt(-174), 'AbsTol', 1e-25);
end

function testRayleighNormalization(testCase)
s = simkit.streams(312); n = 400000;
h = simkit.rayleigh(s.channel, [n,1]);
verifyEqual(testCase, mean(abs(h).^2), 1, 'AbsTol', .01);
end

function testAwgnBpsk(testCase)
s = simkit.streams(312); n = 400000;
z = randn(s.noise,n,1);
for rho = [1,2,4]
    p = .5*erfc(sqrt(rho)); got = mean(1+z/sqrt(2*rho)<0);
    verifyLessThanOrEqual(testCase, abs(got-p), 4*sqrt(p*(1-p)/n));
end
end

function testRayleighOutage(testCase)
s = simkit.streams(312); n = 400000;
g = abs(simkit.rayleigh(s.channel,[n,1])).^2;
for rho = [1,2,4]
    p = -expm1(-1/rho); got = mean(g*rho<1);
    verifyLessThanOrEqual(testCase, abs(got-p), 4*sqrt(p*(1-p)/n));
end
end

function testErgodicRate(testCase)
s = simkit.streams(312); n = 400000;
g = abs(simkit.rayleigh(s.channel,[n,1])).^2;
for rho = [1,2,4]
    values = log2(1+rho*g); theory = exp(1/rho)*expint(1/rho)/log(2);
    verifyLessThanOrEqual(testCase, abs(mean(values)-theory), 4*std(values)/sqrt(n));
end
end

function testOrderedNomaOutage(testCase)
s = simkit.streams(312); n = 400000;
gains = sort(-log(rand(s.channel,n,2)),2);
for rho = [2,10,30]
    [weak,sic,strong] = simkit.nomaSinr(gains(:,1),gains(:,2),rho,.8,0);
    [pw,ps] = simkit.nomaOutage(rho,.8,1,1);
    verifyLessThanOrEqual(testCase, abs(mean(weak<1)-pw), 4*sqrt(pw*(1-pw)/n));
    verifyLessThanOrEqual(testCase, abs(mean(sic<1 | strong<1)-ps), 4*sqrt(ps*(1-ps)/n));
end
end

function testRisIncreasingApertureScaling(testCase)
% Unit-variance independent paths; aperture grows with element count.
s = simkit.streams(312); sizes = [64,128,256,512]; powers = zeros(size(sizes));
for i = 1:numel(sizes)
    g = simkit.rayleigh(s.channel,[4000,sizes(i)]);
    h = simkit.rayleigh(s.channel,[4000,sizes(i)]);
    powers(i) = mean(abs(simkit.risCascade(g,h)).^2);
end
fit = polyfit(log(sizes),log(powers),1);
verifyGreaterThanOrEqual(testCase, fit(1), 1.9);
verifyLessThanOrEqual(testCase, fit(1), 2.1);
end

function testSeedReproducibility(testCase)
a = simkit.streams(10); b = simkit.streams(10);
verifyEqual(testCase, simkit.rayleigh(a.channel,[10,1]), simkit.rayleigh(b.channel,[10,1]));
end

% Wind Data Processing %
clear all
close all
%%
%==============================
% Parameter Setup
%==============================
zr     = 10 ;     %  [m] reference height for wind measurement
zt     = 83.5 ;   %  [m] elevation of wind turbine
apha   = 0.11;    %  the power law exponent (emperical number 0.11 for ocean, 0.143 for land)
rhostd   = 1.225;
rhozt   = rhostd-(1.194E-4)*zt; % air density at the height of zt
%%
fid = fopen('44020h2011.txt','r');
%windat = fscanf(fid,'%d%d%d%d%d%d %f%f%f%f%f %d %f%f%f%f%f%f',3);
wintxt = textscan(fid,'%s %*[^\n]',2) ; % read head info
windat = textscan(fid,'%f%f%f%f%f%f %f%f%f%f%f %f %f%f%f%f%f%f',inf);
date.yr = cell2mat(windat(1,1));
date.mon = cell2mat(windat(1,2));
date.day = cell2mat(windat(1,3));
date.hr = cell2mat(windat(1,4));
date.min = cell2mat(windat(1,5));
date.sec = cell2mat(windat(1,5)).*0.0;
wind.dir = cell2mat(windat(1,6));
wind.spd = cell2mat(windat(1,7)); % wind speed at a referecne height 
% Calculate Julian Day
jdaya = datenum(date.yr,date.mon,date.day,date.hr,date.min,date.sec) ;
jday0 = datenum(date.yr(1),date.mon(1),date.day(1),date.hr(1),date.min(1),date.sec(1));
jday = jdaya-jday0;
% Estimate wind speed at wind turbine elelevation (zt), using Wind Profile Law  
wind.spdzt = wind.spd*(zt/zr)^apha;  
%
idx = find(wind.spdzt == 0.0); 
wind.spdzt(idx) = 0.000001;
%
subplot(2,1,1)
plot(jday,wind.spdzt,'k');
xlabel ('Days in 2011');
ylabel (['Wind Speed at' num2str(zt) '(m/s)']);
xlim([0 365]);
ylim([0 30]);
%
%% Probability Density Function
wbinwidth = 1;
wspdbin = 0:wbinwidth:30; % Wind spdeed bin
nwind = length(wind.spdzt);
counts = hist(wind.spdzt,wspdbin);
wprob = counts / (nwind * wbinwidth);
%
subplot(2,1,2)
bar(wspdbin,wprob,'hist'); hold on
h = get(gca,'child');
set(h,'FaceColor',[.9 .9 .9]);
% xlabel('Wind Speed'); ylabel('Probability Density'); ylim([0 0.15]);
%****************************************************************
% Weibull parameter estimates [c,k] or [a,b];
%    paramEsts(c,k) = wblfit(wspd); c=scale parameter, k=shape parameter
% Computes the Weibull pdf at each of the values in X using c, k
%    Y = wblpdf(X,c,k): Weibull probalility density function
%****************************************************************
% wspdbin = linspace(0,25,26);  % y = linspace(a,b,n) generates a row vector y of n points linearly 
paramEsts = wblfit(wind.spdzt); % Weibull parameter estimates
pdfWSPD   = wblpdf(wspdbin,paramEsts(1),paramEsts(2)); % Weibull pdf
% subplot(2,1,2)
line(wspdbin,pdfWSPD,'linewidth',3); hold off
xlabel('Wind Speed (m/s)'); ylabel('Probability Density'); xlim([-0.5 25]); ylim([0 0.15]);
fclose(fid);
pause
close gcf
%%
%==========================================
% Wind Power Resouce Estimate
%==========================================
Pyr = 1/nwind*0.5*rhozt*sum(wind.spdzt.^3);      % W/m2 Wind Power Density(WPD)using time series data
PyrWPDF = 0.5*rhozt*sum(pdfWSPD.*wspdbin.^3);  % W/m2 Wind Power Density(WPD)using Weibull PDF
%%
%==========================================
% Wind Energy Estimate
%==========================================
%% Polynomical Model of Wind Turbine Power Curve, [Eq. 8 in Jafaria 2010 ]
% Input = Vin, Vout, Vr, Pr, m
%-------------------------------
Vin    = 4;     % [0-7 m/s], cut-in speed
Vr     = 14;    % Rated speed 
Vout   = 25;    % [10-25 m/s], cut-out speed
Ctot   = 0.35;  % [10-59%], Power efficiency
Pr     = 3.6;   % [MW] Wind Turbine Rated Power
m      = 2;     % 1 or 2 
%-------------------------------------------
% Power Curve Calculation
%-------------------------------------------
Pv   = wspdbin.*0; % Power Curve
idx1 = find(wspdbin<Vin | wspdbin>Vout );
idx2 = find(wspdbin>=Vin & wspdbin<=Vr);
idx3 = find(wspdbin>Vr & wspdbin<=Vout); 
Pv(idx1) = 0.0;
Pv(idx2) = Pr*(wspdbin(idx2).^m-Vin^m)/(Vr^m-Vin^m); 
Pv(idx3) = Pr;
%
subplot(2,1,1)
plot(wspdbin,Pv,'-b');
xlabel ('Wind Speed (m/s)');
ylabel ('Wind Power Output (kW)');
pause
%-------------------------------------------
% Harvested Wind Energy
%-------------------------------------------
% Based on time series wind data%
idx1 = find(wind.spdzt<Vin | wind.spdzt>Vout );
idx2 = find(wind.spdzt>=Vin & wind.spdzt<=Vr);
idx3 = find(wind.spdzt>Vr & wind.spdzt<=Vout); 
Pw(idx1)   =  0.0; 
Pw(idx2)   =  (wind.spdzt(idx2).^m-Vin^m)/(Vr^m-Vin^m); 
Pw(idx3)   =  1.0;
Ew   = Pr*(rhozt/rhostd)*Pw;  % [MWhr(i=1,nhr)
Esum = sum(Ew); % [MWhr/yr]
Eavg = mean(Ew);
% length(idx1)+length(idx2)+length(idx3)
% pause 
%-----------------------
% Based on Weibull PDF
%-----------------------
idx1 = find(wspdbin<Vin | wspdbin>Vout );
idx2 = find(wspdbin>=Vin & wspdbin<=Vr);
idx3 = find(wspdbin>Vr & wspdbin<=Vout); 
Pwpdf(idx1) = 0.0;
Pwpdf(idx2) = nwind*(wspdbin(idx2).^m-Vin^m)/(Vr^m-Vin^m).*pdfWSPD(idx2); 
Pwpdf(idx3) = nwind*1.0*pdfWSPD(idx3);
Ewpdf       = Pr*(rhozt/rhostd)*Pwpdf; % % [MWhr(j=1,nbin)
Esumpdf     = sum(Ewpdf)% [MWhr/yr]
Eavgpdf     = Esumpdf/nwind;
CF          = Esumpdf / (nwind*Pr)*100.0;
% length(idx1)+length(idx2)+length(idx3)









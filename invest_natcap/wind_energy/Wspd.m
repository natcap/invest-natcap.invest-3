clear all
% output file name
fout = ['../Output/NewEngland_WINPAR.txt'];
fidout = fopen(fout,'w');
fprintf(fidout,'%s,%s,%s,%s,%s,%s,%s,%s\n', ...
       'ID','LONG','LATI','IST','JST','WblRamda','WblK','DataCOVpct');
% READ GRID INFO
[N1,N2,ALON,ALAT,IST,JST]  = textread('../WinProF/NewEngland_IJ.txt','%d %d %f %f %d %d ','headerlines',1); 
% INITIALIZE
iSAVE = 0;
NT   = 20680;
NST  = 21549; % 
WIN.U = zeros(NST,1);
WIN.V = zeros(NST,1); 
%
for ii = 1:1000:NST  
% READ WIND DATA
fidWU = fopen('..\Output\NewEnglandwindU.bin'); % OPEN INPUT DATA
fidWV = fopen('..\Output\NewEnglandwindV.bin'); % OPEN INPUT DATA 
%
NST1 = ii;      % Starting ST#
NST2 = ii+1000-1;   % Ending ST#  NST2-NST should be 1000 
if(NST2>NST); NST2=NST; end
NST2
%%
WIN.SPD = zeros(NST2-NST1+1,NT); % 2D(NST,NT)
for i=1:NT
    % while ~feof(fidWU)   % Time Step   
    % READ U
    WIN.nU=fread(fidWU, [1,1],'int');   
    WIN.U=fread(fidWU, [NST,1],'float');
    % READ V    
    WIN.nV=fread(fidWV, [1,1],'int');   
    WIN.V=fread(fidWV, [NST,1],'float');  
    %ST3WD(i,1) = WIN.U(1122,1);
    %ST3WD(i,2) = WIN.V(1122,1);
    %ST4WD(i,1) = WIN.U(1031,1);
    %ST4WD(i,2) = WIN.V(1031,1);
    % uu, vv, win.spd = dimension size is same
    uu = WIN.U(NST1:NST2,1).*WIN.U(NST1:NST2,1); 
    vv = WIN.V(NST1:NST2,1).*WIN.V(NST1:NST2,1); 
    WIN.SPD(:,i) = sqrt(uu+vv);   % wind speed
    %
    idx = (uu>=(30.0^2))|(vv>=(30.0^2)); 
    WIN.SPD(idx,i) = NaN; % Dummy Data
    idx = (uu==0.0 & vv==0.0);  
    WIN.SPD(idx,i)=0.00001; % WSPD = 0
end 

% save(fwspd, 'WIN');  
%-------------------------
% Grid Info b/w NST1 and NST2
IST2 = IST(NST1:NST2); 
JST2 = JST(NST1:NST2); 
ALON2 = ALON(NST1:NST2); 
ALAT2 = ALAT(NST1:NST2); 
%ADEP2 = ADEP(NST1:NST2); 
%-------------------------
% Time Series Analysis using 
binWidth = 1;
binCtrs = 1:binWidth:30; % Bin Width  
for j = 1:(NST2-NST1+1) % Tric to avoide Out of Memory Error
    iSAVE = iSAVE+1;
    idx = ~isnan(WIN.SPD(j,:));% WIN.SPD(NST,NT)
    wspd = WIN.SPD(j,idx);
    idx = (wspd == 0.0); 
    wspd(idx) = 0.00001; 
    ndat = length(wspd); 
    datcov = ndat/NT*100.0;  % Data Coverage
    if(ndat>0.5*NT)  % 90% Data Coverage
        %visualize wind data is to make a histogram.
        if(0)
            subplot(2,1,1)
            counts = hist(wspd,binCtrs);
            prob = counts / (ndat * binWidth);
            bar(binCtrs,prob,'hist'); hold on
            h = get(gca,'child');
            set(h,'FaceColor',[.9 .9 .9]);
            xlabel('Wind Speed'); ylabel('Probability Density'); xlim([0 30]); ylim([0 0.5]);  
        end
        %########################################################
        % Weibull parameter estimates [c,k] or [a,b];
        % paramEsts(aramda,bk) = wblfit(wspd); a_ramda=scale parameter, bk=shape parameter
        % Computes the Weibull pdf at each of the values in X using c, k
        %    Y = wblpdf(X,c,k): Weibull probalility density function
        %########################################################
        %xgrid = linspace(0,20,100);  % y = linspace(a,b,n) generates a row vector y of n points linearly 
        xgrid = binCtrs; 
        paramEsts = wblfit(wspd); % Weibull parameter estimates
        pdfEst = wblpdf(xgrid,paramEsts(1),paramEsts(2)); % Weibull pdf
        % line(xgrid,pdfEst); hold off
        %
        fprintf(fidout, '%d,%f,%f,%d,%d,%f,%f,%f\n', ...
        iSAVE,ALON2(j),ALAT2(j),IST2(j),JST2(j),paramEsts(1),paramEsts(2),datcov);
    else 
        fprintf(fidout, '%d,%f,%f,%d,%d,%f,%f,%f\n', ...
        iSAVE,ALON2(j),ALAT2(j),IST2(j),JST2(j),-9999.9,-9999.9,datcov);       
    end
end
fclose(fidWU);
fclose(fidWV);
%
end
fprintf(fidout,'END');
fclose(fidout); 


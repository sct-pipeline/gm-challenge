function qualitative_assessment(xlsx_file)
%QUALITATIVE_ASSESSMENT visualizes qualitative assessment of the gm-challenge 
%
% REQUIRED INPUT:
%           xlsx_file ... Excel sheet with the qualitative assessment
%                         The example sheet is available in the same folder as this function is stored.
%
% Example function call in MATLAB GUI:
%           qualitative_assessment('qualitative_assessment.xlsx')
%
% Example function call from terminal creating file figure_qualitative_assessment.png in the current directory:
%           matlab -r "qualitative_assessment('qualitative_assessment.xlsx'),print('figure_qualitative_assessment', '-dpng', '-r300'),pause(0.5),exit"
%
% Authors: Rene Labounek, Marcella Lagana, Julien Cohen-Adad

[~, ~, raw] = xlsread(xlsx_file);

center = raw(2:end,16);

subid = raw(2:end,1);
subid_unique = unique(subid);
subid_unique = subid_unique([4:end 1:3],1);

center_unique = cell(1,1);
for ind = 1:size(subid_unique,1)
    tmp2 = center(strcmp(subid,subid_unique{ind,1}),1);
    center_unique{ind,1} = tmp2{1,1};
end
clear tmp tmp2


field = raw(2:end,9);
fieldid=ones(size(field));
fieldid(strcmp(field,'3T'))=2;
fieldid(strcmp(field,'7T'))=3;

score = cell2mat(raw(2:end,3:7));
score_name =  raw(1,3:7);

scorer = raw(2:end,10);
scorerid = ones(size(scorer));
scorerid(strcmp(scorer,'FB')) = 2;

ind1t=1;
ind3t=1;
ind7t=1;

score1t = [];
score3t = [];
score7t = [];
subid1t = cell(1,1);
subid3t = cell(1,1);
subid7t = cell(1,1);
center1t = cell(1,1);
center3t = cell(1,1);
center7t = cell(1,1);

for ind = 1:size(subid_unique,1)
    pos = strcmp(subid,subid_unique(ind));
    fld = unique(fieldid(pos));    
    if fld == 1
        score1t(:,:,ind1t) = score(pos,:);
        subid1t{ind1t,1} = subid_unique{ind};
        scorerid1t(:,ind1t) = scorerid(pos);
        field1t(ind1t,1) = 1.5;
        center1t{ind1t,1} = center_unique{ind};
        
        ind1t = ind1t+1;
    elseif fld == 2
        score3t(:,:,ind3t) = score(pos,:);
        subid3t{ind3t,1} = subid_unique{ind};
        scorerid3t(:,ind3t) = scorerid(pos);
        field3t(ind3t,1) = 3;
        center3t{ind3t,1} = center_unique{ind};
        
        ind3t = ind3t+1;
    elseif fld == 3
        score7t(:,:,ind7t) = score(pos,:);
        subid7t{ind7t,1} = subid_unique{ind};
        scorerid7t(:,ind7t) = scorerid(pos);
        field7t(ind7t,1) = 7;
        center7t{ind7t,1} = center_unique{ind};
        
        ind7t = ind7t + 1;
    end 
end

score = cat(3,score1t,score3t);
score = cat(3,score,score7t);

subid = [subid1t; subid3t; subid7t];
center = [center1t; center3t; center7t];

scorer = [scorerid1t scorerid3t scorerid7t];

field = [field1t; field3t; field7t]';
clear score1t score3t score7t subid1t subid3t subid7t scorerid1t scorerid3t scorerid7t field1t field3t field7t ind1t ind3t ind7t ind fld
clear scorerid fieldid subid_unique
clear center1t center3t center7t

grp = 1:size(score,3);
grp = repmat(grp,size(score,1),1);

pos3T = find(field==3,1);
pos7T = find(field==7,1);

spearman = zeros(size(score,2),1);
p_spearman = zeros(size(score,2),1);
h.fig = figure(1);
set(h.fig,'Position',[50 50 2200 1200])
for ind = 1:size(score,2)
    data = squeeze(score(:,ind,:));
    [spearman(ind), p_spearman(ind)]=corr(data(scorer==1),data(scorer==2),'Type','Spearman');
    
    if ind < size(score,2)
        subplot(3,2,ind+2)
    else
        subplot(3,2,1)
    end
    plot([pos3T-0.5 pos3T-0.5],[0.5 5.5],'k:','LineWidth',3)
    hold on
    plot([pos7T-0.5 pos7T-0.5],[0.5 5.5],'k:','LineWidth',3)
    plot([unique(grp)-0.45 unique(grp)+0.45]', repmat(median(data)',1,2)','c-','LineWidth',6)
    scatter(grp(scorer==1), data(scorer==1),60, 'kx', 'jitter','on', 'jitterAmount', 0.24,'MarkerEdgeAlpha',0.5,'Linewidth',3);
    scatter(grp(scorer==2), data(scorer==2),60, 'rd', 'jitter','on', 'jitterAmount', 0.24,'MarkerEdgeAlpha',0.5,'Linewidth',3);
    hold off
    text(1.5,4.5,'1.5T','FontSize',14,'HorizontalAlignment', 'center')
    text(5.5,4.5,'3.0T','FontSize',14,'HorizontalAlignment', 'center')
    text(11.0,4.5,'7.0T','FontSize',14,'HorizontalAlignment', 'center')
    if p_spearman(ind)>=0.001
        text(13.4,1.4,['r=' num2str(spearman(ind),'%.3f') '; p_r=' num2str(p_spearman(ind),'%.3f')],'FontSize',14,'HorizontalAlignment', 'right')
    else
        text(13.4,1.4,['r=' num2str(spearman(ind),'%.3f') '; p_r<0.001'],'FontSize',14,'HorizontalAlignment', 'right')
    end
    title(score_name{1,ind})
    
    axis([0.5 13.5 0.7 5.3])
    grid on
    if ind == size(score,2)
        set(gca,'FontSize',14,'LineWidth',2,'Xtick',1:size(score,3),'XTickLabel',center','Color',[255 255 224]/255)
    else
        set(gca,'FontSize',14,'LineWidth',2,'Xtick',1:size(score,3),'XTickLabel',center')
    end
    xtickangle(45)
end

subplot(3,2,2)
scatter(grp(scorer==1), data(scorer==1),60, 'kx', 'jitter','on', 'jitterAmount', 0.24,'MarkerEdgeAlpha',0.5,'Linewidth',3);
hold on
scatter(grp(scorer==2), data(scorer==2),60, 'rd', 'jitter','on', 'jitterAmount', 0.24,'MarkerEdgeAlpha',0.5,'Linewidth',3);
plot([unique(grp)-0.45 unique(grp)+0.45]', repmat(median(data)',1,2)','c-','LineWidth',6)
hold off
legend('Scorer 1','Scorer 2','median','Location','southwest')
set(gca,'FontSize',18,'LineWidth',2)
axis([-10 -5 -10 -5])
axis off
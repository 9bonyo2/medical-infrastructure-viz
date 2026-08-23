import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd 
df=pd.read_csv(r'C:\Users\이주혁\Desktop\pediatric\data\pediatric\processed\ped_stats.csv')
plt.rc('font',family='Malgun Gothic')
regions = df['지역'].unique()
fig, axes = plt.subplots(2, 1, figsize=(15, 10))
for region in regions:
    region_df = df[df['지역'] == region].sort_values('시점')
    axes[0].plot(region_df['시점'],region_df['의원1개당전문의수'],marker='o',label=region)
    axes[1].plot(region_df['시점'],region_df['아동1만명당전문의수'],marker='o',label=region)

axes[0].set_title('지역별 소아과 의원 1개당 전문의 수 변화')
axes[0].set_xlabel('연도')
axes[0].set_ylabel('의원 1개당 전문의 수')
axes[0].grid(alpha=0.3)
axes[0].legend(bbox_to_anchor=(1,1),loc='upper left')

axes[1].set_title('지역별 아동 1만 명당 소아과 전문의 수 변화')
axes[1].set_xlabel('연도')
axes[1].set_ylabel('아동 1만 명당 전문의 수')
axes[1].grid(alpha=0.3)
axes[1].legend(bbox_to_anchor=(1,1),loc='upper left')

plt.tight_layout()
plt.show()
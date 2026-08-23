import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd 
df=pd.read_csv(r'C:\Users\이주혁\Desktop\pediatric\data\pediatric\processed\ped_stats.csv')
plt.rc('font',family='Malgun Gothic')
years=df['시점'].unique()
for year in years:
    df_year=df[df['시점']==year]
    fig,ax=plt.subplots(2,1,figsize=(15,10))
    sns.barplot(data=df_year,x='지역',y='의원1개당전문의수',ax=ax[0],hue='지역')
    ax[0].set_title(f'{year}년도 각 지역의 의원1개당 전문의수')
    ax[0].set_xlabel('지역')
    ax[0].set_ylabel('의원1개당전문의수')

    sns.barplot(data=df_year,x='지역',y='아동1만명당전문의수',hue='지역')
    ax[1].set_title(f'{year}년도 각 지역의 아동1만명당 전문의수')
    ax[1].set_xlabel('지역')
    ax[1].set_ylabel('아동1만명당 전문의수')

    plt.tight_layout()
    plt.show()
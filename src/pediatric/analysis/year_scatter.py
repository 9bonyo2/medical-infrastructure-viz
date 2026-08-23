import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
df=pd.read_csv(r'C:\Users\이주혁\Desktop\pediatric\data\pediatric\processed\ped_stats.csv')
plt.rc('font',family='Malgun Gothic')
years=df['시점'].unique()

for year in years:

    plot_df=df[df['시점'] == year]
    # 연도별 중앙값
    x_median = plot_df['의원1개당전문의수'].median()
    y_median = plot_df['아동1만명당전문의수'].median()



    plt.figure(figsize=(12, 8))

    sns.scatterplot(
        data=plot_df,
        x='의원1개당전문의수',
        y='아동1만명당전문의수',
        s=130,
        color='#4C72B0'
    )

    # 지역명 표시
    for _, row in plot_df.iterrows():
        plt.annotate(row['지역'],(row['의원1개당전문의수'],row['아동1만명당전문의수']),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=9
        )

    # 연도별 중앙값 기준선
    plt.axvline(
        x=x_median,
        color='red',
        linestyle='--',
        linewidth=1.5,
        label=f'의원당 전문의 중앙값: {x_median:.2f}'
    )

    plt.axhline(
        y=y_median,
        color='green',
        linestyle='--',
        linewidth=1.5,
        label=f'아동 1만 명당 중앙값: {y_median:.2f}'
    )

    plt.title(
        f'{int(year)}년 지역별 소아과 공급 역량\n',
        fontsize=15
    )

    plt.xlabel('의원 1개당 소아청소년과 전문의 수')
    plt.ylabel('아동 1만 명당 소아청소년과 전문의 수')
    plt.legend()
    plt.tight_layout()
    plt.show()
import pandas as pd
from functools import reduce

d1=pd.read_csv(r'C:\Users\이주혁\Desktop\pediatric\data\pediatric\raw\KOSIS_hospital_raw.csv',encoding='utf-8')
d2=pd.read_csv(r'C:\Users\이주혁\Desktop\pediatric\data\pediatric\raw\KOSIS_baby_number_raw.csv',encoding='utf-8',skiprows=[1])
d3=pd.read_csv(r'C:\Users\이주혁\Desktop\pediatric\data\pediatric\raw\KOSIS_doctor_raw.csv',encoding='utf-8')
d4=pd.read_csv(r'C:\Users\이주혁\Desktop\pediatric\data\pediatric\raw\KOSIS_birthrate_raw.csv',encoding='utf-8')
d5=pd.read_csv(r'C:\Users\이주혁\Desktop\pediatric\data\pediatric\raw\KOSIS_children_number_raw.csv',encoding='utf-8')

d1['연도']=(d1['시점'].str.extract(r'(\d{4})')[0].astype(int))
d1=d1.rename(columns={'시군구별(1)':'지역'})
df_hos=(d1.loc[d1['지역']!='전체'].groupby(['연도','지역'],as_index=False)['소아청소년과'].mean())
df_hos['지역']=df_hos['지역'].replace({'서울':'서울특별시','부산':'부산광역시','대구':'대구광역시','인천':'인천광역시','광주':'광주광역시','대전':'대전광역시','울산':'울산광역시','세종':'세종특별자치시','경기':'경기도','강원':'강원특별자치도','충남':'충청남도','충북':'충청북도','경남':'경상남도','경북':'경상북도','전북':'전북특별자치도','전남':'전라남도','제주':'제주특별자치도'})
df_hos=df_hos.rename(columns={'연도':'시점','소아청소년과':'소아청소년과의원수'})

d2=d2.rename(columns={'행정구역별':'지역'})
df_bn=pd.melt(d2,id_vars='지역',var_name='시점',value_name='출생아수')
df_bn=df_bn.dropna(subset=['시점','출생아수'])
df_bn=df_bn[df_bn['지역']!='전국'].reset_index(drop=True)
df_bn['출생아수'] = pd.to_numeric(df_bn['출생아수'],errors='coerce').astype('Int64')
df_bn['시점'] = pd.to_numeric(df_bn['시점'],errors='coerce').astype('Int64')

d3['연도']=(d3['시점'].str.extract(r'(\d{4})')[0].astype(int))
d3=d3.rename(columns={'시군구별(1)':'지역'})
df_doc=(d3.loc[d3['지역']!='전체'].groupby(['연도','지역'],as_index=False)['소아청소년과'].mean())
df_doc['지역']=df_doc['지역'].replace({'서울':'서울특별시','부산':'부산광역시','대구':'대구광역시','인천':'인천광역시','광주':'광주광역시','대전':'대전광역시','울산':'울산광역시','세종':'세종특별자치시','경기':'경기도','강원':'강원특별자치도','충남':'충청남도','충북':'충청북도','경남':'경상남도','경북':'경상북도','전북':'전북특별자치도','전남':'전라남도','제주':'제주특별자치도'})
df_doc=df_doc.rename(columns={'연도':'시점','소아청소년과':'소아청소년과전문의수'})

d4=d4.rename(columns={'데이터':'출산율'})
d4=d4.rename(columns={'시군구별':'지역'})
df_ped=d4.loc[d4['지역']!='전국',['지역','시점','출산율']].reset_index(drop=True)

d5=d5.rename(columns={'행정구역(동읍면)별':'지역'})
df_ch=d5.loc[d5['지역']!='전국',['시점','지역','항목','0 - 4세','5 - 9세','10 - 14세']].reset_index(drop=True)
age=['0 - 4세','5 - 9세','10 - 14세']
df_ch['아동인구수(0-14세)']=df_ch[age].sum(axis=1)
df_ch=df_ch.drop(age,axis=1)
df_ch=df_ch.drop('항목',axis=1)

list=[df_hos,df_ped,df_bn,df_ch,df_doc]
result=reduce(lambda df1,df2:pd.merge(df1,df2,on=['시점','지역'],how='inner'),list)
result=result[result['시점']!=2025]
result['의원1개당전문의수']=result['소아청소년과전문의수']/result['소아청소년과의원수']
result['아동1만명당전문의수']=result['소아청소년과전문의수']/result['아동인구수(0-14세)']*10000

result.to_csv(r'C:\Users\이주혁\Desktop\pediatric\data\pediatric\processed\ped_stats.csv',index=False)



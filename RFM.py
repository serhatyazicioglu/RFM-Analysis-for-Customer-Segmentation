import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt

pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', lambda x: '%.5f' % x)
df_ = pd.read_excel("online_retail_II.xlsx", sheet_name="Year 2010-2011")
df = df_.copy()

df.info()
df.isnull().sum()

# boş değerleri kaldırmak
df.dropna(inplace=True)

# ürünlerin adet sayıları
df["Description"].value_counts().head()

# essiz ürün sayısı
df["Description"].nunique()

# ürünlerin toplam satıs miktarını çoktan aza doğru sıralamak
df.groupby("Description").agg({"Quantity": "sum"}).sort_values("Quantity", ascending=False).head()

# kesilen fatura adedi
df["Invoice"].nunique()

# iade ürünleri işlemlere dahil etmemek için eledik
df = df[~df["Invoice"].str.contains("C", na=False)]

# her bir üründen kazanılan ücreti hesaplamak için bir değişken atadık
df["TotalPrice"] = df["Quantity"] * df["Price"]

# veri setinin son halinde bir aykırılık olup olmadığını kontrol ediyoruz
df.describe([0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]).T

# veri setindeki son tarihe baktık
df["InvoiceDate"].max()
"""
Recency değerini hesaplamak için today_date adlı bir değişken tanımladık.
Bu değişkenin verideki son tarihten 2 gün fazla yaptık. Bunu yapma amacımız veri setindeki
son tarihte alışveriş yapanların Recency değerinin 0 olmasını engellemekti.
"""
today_date = dt.datetime(2011, 12, 11)

# gruplama ile rfm değerlerini elde ettik
rfm = df.groupby('Customer ID').agg({'InvoiceDate': lambda date: (today_date - date.max()).days,
                                     'Invoice': lambda num: len(num),
                                     'TotalPrice': lambda TotalPrice: TotalPrice.sum()})

rfm.columns = ['Recency', 'Frequency', 'Monetary']

# satın alma olduğu halde ücret gözükmeyen problemli verileri kaldırdık.
rfm = rfm[(rfm["Monetary"]) > 0 & (rfm["Frequency"] > 0)]

"""
Recency değerini segmentlere ayırdık. 
Recency değerinin yüksek olması müşterinin bizden uzaklaşması anlamına geliyor.
Bu karışıklığı önlemek adına labellerini azalan şekilde yaptık
"""
rfm["RecencyScore"] = pd.qcut(rfm["Recency"], 5, labels=[5, 4, 3, 2, 1])
rfm["FrequencyScore"] = pd.qcut(rfm["Frequency"], 5, labels=[1, 2, 3, 4, 5])
rfm["MonetaryScore"] = pd.qcut(rfm["Monetary"], 5, labels=[1, 2, 3, 4, 5])

# rfm değerini tek noktada görmek adına rfm_score adlı değişken tanımladık
rfm["RFM_SCORE"] = (rfm['RecencyScore'].astype(str) +
                    rfm['FrequencyScore'].astype(str) +
                    rfm['MonetaryScore'].astype(str))

seg_map = {
    r'[1-2][1-2]': 'Hibernating',
    r'[1-2][3-4]': 'At_Risk',
    r'[1-2]5': 'Cant_Loose',
    r'3[1-2]': 'About_to_Sleep',
    r'33': 'Need_Attention',
    r'[3-4][4-5]': 'Loyal_Customers',
    r'41': 'Promising',
    r'51': 'New_Customers',
    r'[4-5][2-3]': 'Potential_Loyalists',
    r'5[4-5]': 'Champions'
}
# regex kullanarak rfm değerlerine karşılıkları olan segmentleri verdik
rfm["Segment"] = (rfm['RecencyScore'].astype(str) + rfm['FrequencyScore'].astype(str))
rfm["Segment"] = rfm["Segment"].replace(seg_map, regex=True)

# rfm değerlerini segmentlere göre gruplayıp değerlerinin ortalamasını ve sayısını aldık.
rfm[["Segment", "Recency", "Frequency", "Monetary"]].groupby("Segment").agg(["mean", "count"])

# Loyal_Customers segmentindeki kişilerin değerlerini alıp csv dosyası olarak export ettik.
rfm[rfm["Segment"] == "Loyal_Customers"].index

new_df = pd.DataFrame()
new_df["Loyal_Customers"] = rfm[rfm["Segment"] == "Loyal_Customers"].index
new_df.to_csv("Loyal_Customers.csv")


%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffffff'}}}%%
flowchart TD
    Transfo_T1["⚡ <b>Transfo T1</b><br/>Ik3 = 22.7 kA"]
    Transfo_T1 --> |"MCCB-TM250D-36kA<br/>70/35/35 mm²"| TGBT["<b>TGBT</b><br/>Ik3=20.9kA | Ik1=16843A<br/>ΔU=0.2%"]
    TGBT --> |"MCCB-TM32D-36kA<br/>4/4/4 mm²"| Moteur_M1___18_5kW["<b>Moteur M1 - 18.5kW</b><br/>Ik3=0.9kA | Ik1=418A<br/>ΔU=3.2%"]
    TGBT --> |"MCCB-TM63D-36kA<br/>10/10/10 mm²"| TD1_Bureau["<b>TD1 Bureau</b><br/>Ik3=1.9kA | Ik1=921A<br/>ΔU=2.4%"]
    TD1_Bureau --> |"MCB-16A-CourbeC-10kA<br/>4/4/4 mm²"| Éclairage_Bureau["<b>Éclairage Bureau</b><br/>Ik3=0.7kA | Ik1=342A<br/>ΔU=5.2%"]
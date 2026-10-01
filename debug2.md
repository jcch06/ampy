%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffffff'}}}%%
flowchart TD
    N0["⚡ <b>Transfo T1</b><br/>Ik3 = 22.7 kA"]
    N0 --> |"MCCB-TM250D-36kA<br/>70/35/35 mm²"| N1["<b>TGBT</b><br/>Ik3=20.9kA | Ik1=16843A<br/>ΔU=0.2%"]
    N1 --> |"MCCB-TM32D-36kA<br/>4/4/4 mm²"| N2["<b>Moteur M1 - 18.5kW</b><br/>Ik3=0.9kA | Ik1=418A<br/>ΔU=3.2%"]
    N1 --> |"MCCB-TM63D-36kA<br/>10/10/10 mm²"| N3["<b>TD1 Bureau</b><br/>Ik3=1.9kA | Ik1=921A<br/>ΔU=2.4%"]
    N3 --> |"MCB-16A-CourbeC-10kA<br/>4/4/4 mm²"| N4["<b>Éclairage Bureau</b><br/>Ik3=0.7kA | Ik1=342A<br/>ΔU=5.2%"]
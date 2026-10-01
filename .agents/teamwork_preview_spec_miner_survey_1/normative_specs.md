# Normative Specification: NF C 15-100 (Part 5-52) & UTE C 15-105 Cable Sizing Engine

**Author**: `teamwork_preview_spec_miner_survey_1`  
**Date**: 2026-09-30  
**Status**: Authoritative Normative Specification  
**Governing Standards**:
- **NF C 15-100** (Partie 5-52: Choix et mise en œuvre des matériels — Canalisations)
- **UTE C 15-105** (Guide pratique — Détermination des sections de conducteurs et choix des dispositifs de protection)
- **IEC 60364-5-52** (Low-voltage electrical installations — Part 5-52: Selection and erection of electrical equipment — Wiring systems)
- **IEC 60364-4-43** (Protection against overcurrent)

---

## 1. Design Operating Current ($I_b$)

The design operating current $I_b$ is the continuous current intended to be carried by the circuit in normal service.

### 1.1 Fundamental Formulas

| System Type | Input Given | Exact Formula | Units & Variable Definitions |
| :--- | :--- | :--- | :--- |
| **Single-phase** ($V_n = 230\text{ V}$) | Active Power $P$ (kW) | $$I_b = \frac{P \times 1000}{V_n \times \cos\varphi}$$ | $P$ in kW, $V_n$ in V (default 230 V), $\cos\varphi$ dimensionless ($0 < \cos\varphi \le 1.0$) |
| **Single-phase** ($V_n = 230\text{ V}$) | Apparent Power $S$ (kVA) | $$I_b = \frac{S \times 1000}{V_n}$$ | $S$ in kVA, $V_n$ in V (default 230 V) |
| **Single-phase** ($V_n = 230\text{ V}$) | Direct Current $I$ (A) | $$I_b = I$$ | $I$ in A ($I > 0$) |
| **Three-phase** ($U_n = 400\text{ V}$) | Active Power $P$ (kW) | $$I_b = \frac{P \times 1000}{\sqrt{3} \times U_n \times \cos\varphi}$$ | $P$ in kW, $U_n$ in V (default 400 V), $\cos\varphi$ dimensionless |
| **Three-phase** ($U_n = 400\text{ V}$) | Apparent Power $S$ (kVA) | $$I_b = \frac{S \times 1000}{\sqrt{3} \times U_n}$$ | $S$ in kVA, $U_n$ in V (default 400 V) |
| **Three-phase** ($U_n = 400\text{ V}$) | Direct Current $I$ (A) | $$I_b = I$$ | $I$ in A ($I > 0$) |
| **Direct Current (DC)** | Active Power $P$ (kW) | $$I_b = \frac{P \times 1000}{U_{dc}}$$ | $P$ in kW, $U_{dc}$ in V |
| **Direct Current (DC)** | Direct Current $I$ (A) | $$I_b = I$$ | $I$ in A |

#### Default & Standard Values
- Standard single-phase nominal voltage: $V_n = 230\text{ V}$ (Phase-Neutral).
- Standard three-phase nominal line-to-line voltage: $U_n = 400\text{ V}$ ($U_n = \sqrt{3} \times V_n$).
- Default industrial motor power factor: $\cos\varphi = 0.80$ (typical full-load motor: $0.80 - 0.85$; resistive heating: $1.0$; lighting LED/electronic: $0.90 - 0.95$).

---

### 1.2 Neutral Current and Harmonic Considerations (UTE C 15-105 §4.2 / IEC 60364-5-52 Annex E)

In three-phase balanced systems supplying non-linear loads (LED drivers, power supplies, variable speed drives, computers), third-harmonic currents ($h_3 = 150\text{ Hz}$) and its odd multiples (9, 15, 21...) are in zero-sequence and add up arithmetically in the neutral conductor:
$$I_N = 3 \times I_{h3} = 3 \times \text{THD}_{3} \times I_{\text{phase}}$$

#### Normative Sizing Rule (IEC 60364-5-52 Table E.52.1 & NF C 15-100 §523.5)

| Third Harmonic Ratio ($i_{h3} = \frac{I_{h3}}{I_b}$) | Neutral Dimensioning Rule | Cable Sizing Basis | Reduction / Derating Factor ($k_h$) |
| :---: | :--- | :--- | :---: |
| **$i_{h3} \le 15\%$** | $S_N \ge S_{\text{phase}}$ (or reduced neutral $S_N = S/2$ allowed if $S \ge 16\text{ mm}^2$ Cu / $25\text{ mm}^2$ Al per NF C 15-100 §524.2) | Phase current $I_b$ | **$k_h = 1.00$** |
| **$15\% < i_{h3} \le 33\%$** | $S_N = S_{\text{phase}}$ mandatory. | Phase current $I_b$ | **$k_h = 0.86$** (Cable sized for $I'_z \ge \frac{I_b}{0.86}$) |
| **$33\% < i_{h3} \le 45\%$** | $S_N = S_{\text{phase}}$ mandatory. Neutral current exceeds phase current ($I_N > I_b$). | Neutral current $I_N = 3 \times i_{h3} \times I_b$ | **$k_h = 0.86$** (Cable sized for $I'_z \ge \frac{I_N}{0.86}$) |
| **$i_{h3} > 45\%$** | $S_N \ge S_{\text{phase}}$ mandatory. Severe neutral overload. | Neutral current $I_N = 3 \times i_{h3} \times I_b$ | **$k_h = 1.00$** (Cable sized for $I'_z \ge I_N$) |

---

## 2. Reference Installation Methods (NF C 15-100 Table 52C & 52G / UTE C 15-105 Table BB & BC)

Normative heat dissipation depends on how the cable is physically installed. The standards define standardized Reference Method Letters: **B, C, E, F** (in air) and **D** (underground).

### 2.1 Standard Reference Method Letters

| Method Letter | Standard Definition (NF C 15-100 / IEC 60364-5-52) | Typical Physical Installations |
| :---: | :--- | :--- |
| **B** | Conductors or cables in conduits, trunking, or ducting mounted on a wall or embedded in building materials. | - Insulated conductors in conduit surface mounted (B1)<br>- Multicore cable in conduit surface mounted (B2)<br>- Cables in skirting trunking, flush floor trunking, or building voids |
| **C** | Single-core or multicore cables affixed directly to a wooden, masonry, or unperforated metal surface. | - Multicore cable on unperforated cable tray<br>- Multicore cable clipped direct to wall or ceiling<br>- Cables on non-ventilated brackets |
| **E** | Multicore cable in free air, on perforated cable tray, cable ladder, or suspended cleats. | - Multicore cable on horizontal perforated tray (distance to wall $\ge 0.3 \times d$)<br>- Multicore cable on cable ladder or brackets |
| **F** | Single-core cables in free air, touching in trefoil or contiguous flat configuration, on perforated tray or brackets. | - 3 single-core cables in trefoil (touching) on perforated tray<br>- Single-core cables flat touching on tray |
| **D** | Cables installed in underground conduits, ducts, or buried directly in soil. | - Cables in buried conduit/duct (D1/D2)<br>- Cables buried direct in ground with mechanical tile protection |

### 2.2 Standard Installation Method Mapping (Table 52C / 52G)

| NF C 15-100 Method Code | Description of Installation Mode | Reference Letter |
| :---: | :--- | :---: |
| **Method 1** | Insulated conductors in conduit in thermally insulated wall | A1 |
| **Method 2** | Multicore cable in conduit in thermally insulated wall | A2 |
| **Method 3** | Insulated conductors in conduit on wooden or masonry wall | **B (B1)** |
| **Method 4** | Multicore cable in conduit on wooden or masonry wall | **B (B2)** |
| **Method 5** | Insulated conductors or cables in trunking on wall (horizontal or vertical) | **B** |
| **Method 11** | Multicore cable fixed directly to wall or ceiling | **C** |
| **Method 12** | Single-core cables fixed directly to wall | **C** |
| **Method 13** | Cables on unperforated cable tray (horizontal or vertical) | **C** |
| **Method 31** | Multicore cable on perforated cable tray (horizontal or vertical) | **E** |
| **Method 32** | Multicore cable on cable ladder rack or cleats | **E** |
| **Method 33** | Single-core cables touching in trefoil on perforated cable tray or ladder | **F** |
| **Method 34** | Single-core cables flat touching on perforated cable tray | **F** |
| **Method 61** | Cables in buried ducts / conduits | **D** |
| **Method 62** | Cables buried directly in soil | **D** |

---

## 3. Normative Correction / Derating Factors ($\prod k_i$)

The permissible continuous current of a cable in its operating environment is:
$$I_z = I_0 \times \prod_{i} k_i = I_0 \times k_1 \times k_2 \times k_3 \times k_4 \times k_h$$

The fictitious required reference current $I'_z$ used to select the cable section from normative tables is:
$$I'_z = \frac{I_n}{\prod k_i} \le I_0$$
where $I_n$ is the nominal rating of the protective device ($I_b \le I_n$).

---

### 3.1 Factor $k_1$: Installation Method Correction Factor (UTE C 15-105 Table BD)

When sizing directly using the reference method letters B, C, E, F, $k_1 = 1.00$.  
When adapting an installation mode to a baseline reference method:

| Configuration | Factor $k_1$ |
| :--- | :---: |
| Conduits embedded in masonry or on wall (Method B) | 1.00 |
| Surface mounted directly on wall (Method C) | 1.00 |
| Perforated cable tray (Method E for multicore, F for single-core) | 1.00 |
| Unperforated cable tray (reduction relative to perforated tray E) | 0.95 |
| Vertical perforated cable ladder | 1.00 |
| Cable suspended on catenary wire | 1.00 |

---

### 3.2 Factor $k_2$: Multi-Circuit / Cable Grouping Reduction Factor (NF C 15-100 Table 52N / UTE C 15-105 Table BJ)

Applies when multiple circuits or multicore cables are installed touching or bunched together.

#### Touching in Single Layer (Jointifs en simple couche)

| Number of Circuits / Multicore Cables ($N$) | Single Layer on Wall, Floor, or Unperforated Tray (Method C) | Single Layer on Perforated Tray or Ladder (Method E / F) | Bunched in Air or in Conduit / Trunking (Method B) |
| :---: | :---: | :---: | :---: |
| **1** | 1.00 | 1.00 | 1.00 |
| **2** | 0.85 | 0.88 | **0.80** |
| **3** | 0.79 | 0.82 | **0.70** |
| **4** | 0.75 | 0.77 | **0.65** |
| **5** | 0.73 | 0.75 | **0.60** |
| **6** | 0.72 | 0.73 | **0.57** |
| **7** | 0.72 | 0.73 | **0.54** |
| **8** | 0.71 | 0.72 | **0.52** |
| **9** | 0.70 | 0.72 | **0.50** |
| **12** | 0.70 | 0.72 | **0.45** |
| **16** | 0.70 | 0.72 | **0.41** |
| **20** | 0.70 | 0.72 | **0.38** |

#### Spaced Cables Rule
If adjacent cables or conduits are separated horizontally by a clear distance $d \ge 1 \times D$ (where $D$ is outer cable diameter):
$$k_2 = 1.00$$

---

### 3.3 Factor $k_3$: Ambient Temperature Correction Factor (NF C 15-100 Table 52K / UTE C 15-105 Table BF)

Reference ambient temperatures:
- **In Air**: $\theta_0 = 30^\circ\text{C}$
- **In Ground**: $\theta_0 = 20^\circ\text{C}$

Maximum admissible continuous conductor temperatures:
- **PVC Insulation**: $\theta_{\max} = 70^\circ\text{C}$
- **XLPE / PR / EPR Insulation**: $\theta_{\max} = 90^\circ\text{C}$

Normative formula:
$$k_3 = \sqrt{\frac{\theta_{\max} - \theta_{\text{ambient}}}{\theta_{\max} - \theta_0}}$$

#### Table 52K — Ambient Temperature Factors (Air, Reference $30^\circ\text{C}$)

| Ambient Temperature ($\theta$) | PVC Insulation ($\theta_{\max} = 70^\circ\text{C}$) | XLPE / PR Insulation ($\theta_{\max} = 90^\circ\text{C}$) |
| :---: | :---: | :---: |
| **10 °C** | 1.22 | 1.15 |
| **15 °C** | 1.17 | 1.12 |
| **20 °C** | 1.12 | 1.08 |
| **25 °C** | 1.06 | 1.04 |
| **30 °C (Reference)** | **1.00** | **1.00** |
| **35 °C** | 0.94 | 0.96 |
| **40 °C** | 0.87 | 0.91 |
| **45 °C** | 0.79 | 0.87 |
| **50 °C** | 0.71 | 0.82 |
| **55 °C** | 0.61 | 0.76 |
| **60 °C** | 0.50 | 0.71 |

---

### 3.4 Additional Correction Factors

#### Factor $k_4$: Soil Thermal Resistivity (Buried Cables, Table 52M)
Reference soil thermal resistivity: $1.0\ \text{K}\cdot\text{m/W}$ (NF C 15-100) or $2.5\ \text{K}\cdot\text{m/W}$ (IEC 60364).

| Soil Nature | Thermal Resistivity (K·m/W) | Factor $k_4$ (NF C 15-100) |
| :--- | :---: | :---: |
| Very wet ground (swamp, high water table) | 0.7 | 1.21 |
| Wet soil | 0.8 | 1.13 |
| **Normal damp soil (Reference)** | **1.0** | **1.00** |
| Dry soil | 1.5 | 0.86 |
| Very dry ground (arid, sand, slag) | 2.0 | 0.76 |
| Extremely dry ground | 2.5 | 0.70 |

#### Factor $k_{\text{prot}}$: Overcurrent Protective Device Coordination (NF C 15-100 §433.1)
- **Circuit Breakers (Disjoncteurs NF EN 60898 / NF EN 60947-2)**:
  Operating current $I_2 \le 1.45 \times I_n$. Condition $I_n \le I_z$ guarantees thermal protection. $k_{\text{prot}} = 1.00$.
- **Fuses (Fusibles gG NF EN 60269)**:
  Conventional fusing current $I_2 = 1.6 \times I_n$ (for $I_n \ge 16\text{ A}$) or $1.9 \times I_n$ (for $I_n < 16\text{ A}$).
  To ensure $I_2 \le 1.45 \times I_z$, the cable must satisfy:
  $$I_z \ge \frac{I_2}{1.45} \implies I_z \ge \frac{1.6}{1.45} I_n \approx 1.103 \times I_n \quad (I_n \ge 16\text{ A})$$
  $$I_z \ge \frac{1.9}{1.45} I_n \approx 1.310 \times I_n \quad (I_n < 16\text{ A})$$
  In UTE C 15-105, a protective device factor $k_p = 1.31$ or $1.10$ is applied: $I'_z = \frac{I_n \times k_p}{\prod k_i}$.

---

## 4. Complete Authoritative Reference Current Tables ($I_0$)

Reference current $I_0$ in Amperes [A] at reference ambient temperature ($\theta_0 = 30^\circ\text{C}$ in air), according to **NF C 15-100 Table 52H / UTE C 15-105 Table BD & BJ / IEC 60364-5-52 Tables B.52.2 to B.52.12**.

---

### 4.1 Copper Conductors (Cu) — Permissible Reference Currents $I_0$ (A)

| Section ($S$ mm²) | B / 2-PVC | B / 3-PVC | B / 2-XLPE | B / 3-XLPE | C / 2-PVC | C / 3-PVC | C / 2-XLPE | C / 3-XLPE | E / 3-PVC | E / 3-XLPE | F / 3-XLPE (trefoil) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1.5** | 16.5 | 15 | 22 | 19.5 | 19.5 | 17.5 | 24 | 22 | 18.5 | 26 | - |
| **2.5** | 23 | 20 | 30 | 26 | 27 | 24 | 33 | 30 | 25 | 36 | - |
| **4** | 30 | 27 | 40 | 35 | 36 | 32 | 45 | 40 | 34 | 49 | - |
| **6** | 38 | 34 | 51 | 44 | 46 | 41 | 58 | 52 | 43 | 63 | - |
| **10** | 52 | 46 | 69 | 60 | 63 | 57 | 80 | 71 | 60 | 86 | - |
| **16** | 69 | 62 | 91 | 80 | 85 | 76 | 107 | 96 | 80 | 115 | 110 |
| **25** | 90 | 80 | 119 | 105 | 112 | 96 | 138 | 119 | 101 | 149 | 146 |
| **35** | 111 | 99 | 146 | 128 | 138 | 119 | 171 | 147 | 126 | 185 | 181 |
| **50** | 133 | 118 | 175 | 154 | 168 | 144 | 209 | 179 | 153 | 225 | 219 |
| **70** | 168 | 149 | 221 | 194 | 213 | 184 | 269 | 229 | 196 | 289 | 281 |
| **95** | 201 | 179 | 265 | 233 | 258 | 223 | 328 | 278 | 238 | 352 | 341 |
| **120** | 232 | 206 | 305 | 268 | 299 | 259 | 382 | 322 | 276 | 410 | 396 |
| **150** | 258 | 225 | 334 | 300 | 344 | 299 | 441 | 371 | 319 | 473 | 456 |
| **185** | 294 | 255 | 384 | 340 | 392 | 341 | 506 | 424 | 364 | 542 | 521 |
| **240** | 344 | 297 | 459 | 398 | 461 | 403 | 599 | 500 | 430 | 641 | 615 |
| **300** | 394 | 339 | 532 | 455 | 530 | 464 | 693 | 576 | 497 | 741 | 709 |

*Note: For Method B, standard tables distinguish between conduit on wall (sub-method B1 for single conductors, B2 for multicore cable). Columns above list Method B2 (conservative multicore); for B1 (insulated conductors), values are slightly higher (e.g. 1.5 mm² PVC 2-cond = 17.5 A, 3-cond = 15.5 A).*

---

### 4.2 Aluminium Conductors (Al) — Permissible Reference Currents $I_0$ (A)

*In French installations, aluminium conductors are permitted for cross-sections $\ge 16\text{ mm}^2$ (industrial) or $\ge 10\text{ mm}^2$ (distribution).*

| Section ($S$ mm²) | B / 3-PVC | B / 2-XLPE | B / 3-XLPE | C / 3-PVC | C / 2-XLPE | C / 3-XLPE | E / 3-XLPE | F / 3-XLPE (trefoil) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **16** | 48 | 72 | 64 | 59 | 84 | 76 | 91 | 86 |
| **25** | 63 | 94 | 84 | 73 | 101 | 90 | 108 | 115 |
| **35** | 77 | 115 | 103 | 90 | 126 | 112 | 135 | 143 |
| **50** | 93 | 138 | 124 | 110 | 154 | 136 | 164 | 174 |
| **70** | 118 | 175 | 156 | 140 | 198 | 174 | 211 | 225 |
| **95** | 142 | 210 | 188 | 170 | 241 | 211 | 257 | 275 |
| **120** | 164 | 242 | 216 | 197 | 280 | 245 | 300 | 321 |
| **150** | 189 | 273 | 240 | 226 | 324 | 283 | 346 | 372 |
| **185** | 215 | 310 | 272 | 256 | 371 | 323 | 397 | 427 |
| **240** | 252 | 363 | 318 | 300 | 439 | 382 | 470 | 507 |
| **300** | 289 | 416 | 364 | 346 | 508 | 440 | 543 | 587 |

---

## 5. Standard Sizing Coordination Logic

### 5.1 Verification Conditions
For any sized circuit, the following three conditions MUST be simultaneously satisfied:

1. **Continuous Current Capacity (NF C 15-100 §433.1)**:
   $$I_b \le I_n \le I_z$$
   where:
   - $I_b$: Design operating current of the circuit.
   - $I_n$: Nominal rated current of the upstream protective device.
   - $I_z$: Permissible current of the selected cable in actual installation conditions ($I_z = I_0 \times \prod k_i$).
   - Equivalent required condition on reference current:
     $$I'_z = \frac{I_n}{\prod k_i} \le I_0(S)$$

2. **Permissible Voltage Drop**:
   $$\Delta U \le \Delta U_{\max}$$

3. **Short-Circuit Thermal Stress Withstand**:
   $$I^2 t \le k^2 S^2 \iff S \ge \frac{\sqrt{I^2 t}}{k}$$

---

### 5.2 Standard Cross-Section Series ($S$)
Standard metric conductor cross-sections recognized by NF C 15-100 / IEC 60228:
$$\mathbf{S \in \{1.5,\ 2.5,\ 4,\ 6,\ 10,\ 16,\ 25,\ 35,\ 50,\ 70,\ 95,\ 120,\ 150,\ 185,\ 240,\ 300\}\text{ mm}^2}$$

### 5.3 Standard Protection Device Ratings Series ($I_n$)
Standard nominal ratings for low-voltage modular circuit breakers and fuses:
$$\mathbf{I_n \in \{1,\ 2,\ 3,\ 4,\ 6,\ 10,\ 16,\ 20,\ 25,\ 32,\ 40,\ 50,\ 63,\ 80,\ 100,\ 125,\ 160,\ 200,\ 250,\ 315,\ 400,\ 500,\ 630\}\text{ A}}$$

---

## 6. Voltage Drop Calculation ($\Delta U$) (UTE C 15-105 §5.3 & NF C 15-100 §525)

### 6.1 Exact Voltage Drop Formula
The absolute voltage drop $\Delta U$ (in Volts) along a line of length $L$ (in meters) is:

$$\mathbf{\Delta U = b \times \left( \rho_1 \times \frac{L}{S} \times \cos\varphi + \lambda \times L \times \sin\varphi \right) \times I_b}$$

where:
- **$b$**: Circuit topology coefficient:
  - **$b = 1$** for Three-phase balanced circuit (line-to-line voltage drop, compared to $U_n = 400\text{ V}$).
  - **$b = 2$** for Single-phase circuit Phase-Neutral or Phase-Phase (compared to $V_n = 230\text{ V}$).
  - **$b = 2$** for Direct Current (DC) two-wire circuit.
- **$\rho_1$**: Conductor linear electrical resistivity at maximum normal service temperature ($\Omega\cdot\text{mm}^2/\text{m}$):
  Under UTE C 15-105 convention ($\rho_1 = 1.25 \times \rho_{20}$):
  - **Copper (Cu)**: $\mathbf{\rho_1 = 0.023\ \Omega\cdot\text{mm}^2/\text{m}}$ ($0.02314\ \Omega\cdot\text{mm}^2/\text{m}$)
  - **Aluminium (Al)**: $\mathbf{\rho_1 = 0.037\ \Omega\cdot\text{mm}^2/\text{m}}$ ($0.03676\ \Omega\cdot\text{mm}^2/\text{m}$)
- **$L$**: One-way circuit length in meters (m).
- **$S$**: Cross-sectional area of conductor in $\text{mm}^2$.
- **$\cos\varphi$**: Load operating power factor ($\sin\varphi = \sqrt{1 - \cos^2\varphi}$).
- **$\lambda$**: Linear reactance of conductors in $\Omega/\text{m}$:
  - Standard value for low-voltage cables: **$\lambda = 0.08\ \text{m}\Omega/\text{m} = 0.00008\ \Omega/\text{m}$** ($8 \times 10^{-5}\ \Omega/\text{m}$).
  - For small cross-sections ($S \le 16\text{ mm}^2$), reactance is negligible compared to resistance: $\lambda = 0\ \Omega/\text{m}$.
- **$I_b$**: Circuit design operating current in Amperes (A).

---

### 6.2 Relative Voltage Drop ($\Delta U\%$)

$$\mathbf{\Delta U\% = 100 \times \frac{\Delta U}{U_{\text{ref}}}}$$
where:
- $U_{\text{ref}} = 230\text{ V}$ for single-phase systems.
- $U_{\text{ref}} = 400\text{ V}$ for three-phase systems.

---

### 6.3 Normative Voltage Drop Limits ($\Delta U_{\max}$) (NF C 15-100 Table 52S)

| Installation Supply Source | Lighting Circuits ($\Delta U_{\max}$) | Other Uses / Power ($\Delta U_{\max}$) |
| :--- | :---: | :---: |
| **Public LV Network (Abonné BT - Tarif Bleu / Jaune)** | **3.0 %** | **5.0 %** |
| **Private HV/LV Substation (Poste privé HT/BT)** | **6.0 %** | **8.0 %** |
| **Motor Starting Transient (Démarrage moteurs)** | — | **10.0 %** (max 15%) |

---

## 7. Short-Circuit Thermal Stress Withstand ($I^2 t \le k^2 S^2$)

### 7.1 Adiabatic Formula (NF C 15-100 §434.5.2 & §543)
For short-circuit durations up to $5\text{ seconds}$, heat dissipation away from the conductor is negligible (adiabatic heating). The thermal withstand condition is:

$$\mathbf{I^2 t \le k^2 S^2 \iff S_{\min} = \frac{\sqrt{I^2 t}}{k}}$$

where:
- **$I^2 t$**: The thermal Joule integral let through by the protective device during the fault clearing time (in $\text{A}^2\cdot\text{s}$).
  - For $t \ge 0.1\text{ s}$: $I^2 t = I_{cc}^2 \times t$.
  - For $t < 0.1\text{ s}$: $(I^2 t)_{\max}$ is obtained directly from the circuit breaker manufacturer's energy limitation curve.
- **$S$**: Conductor cross-section in $\text{mm}^2$.
- **$k$**: Normative material thermal withstand factor (in $\text{A}\cdot\text{s}^{1/2}/\text{mm}^2$):

### 7.2 Values of Factor $k$

| Conductor Metal | Insulation Material | Initial Operating Temp ($\theta_i$) | Final Short-Circuit Temp ($\theta_f$) | Factor $k$ ($\text{A}\cdot\text{s}^{1/2}/\text{mm}^2$) |
| :--- | :--- | :---: | :---: | :---: |
| **Copper (Cu)** | **PVC** | 70 °C | 160 °C | **115** |
| **Copper (Cu)** | **XLPE / PR / EPR** | 90 °C | 250 °C | **143** |
| **Aluminium (Al)** | **PVC** | 70 °C | 160 °C | **76** |
| **Aluminium (Al)** | **XLPE / PR / EPR** | 90 °C | 250 °C | **94** |

---

## 8. Systematic Sizing Algorithm

The automated engine MUST follow this deterministic workflow:

```
[Input: Circuit parameters (Type, Voltage, Power/Current, CosPhi, Length, Method, Grouping, Temp, Soil, Harmonics, dU_max)]
   │
   ▼
1. Calculate Ib:
   Single-phase: Ib = P*1000 / (V * cos_phi)  or  S*1000 / V  or  I
   Three-phase:  Ib = P*1000 / (sqrt(3)*U*cos_phi)  or  S*1000 / (sqrt(3)*U)  or  I
   │
   ▼
2. Determine Protection Rating In:
   Select smallest standard In >= Ib (or take user-specified In).
   │
   ▼
3. Determine Cumulative Derating Factor prod(ki):
   prod(ki) = k1 * k2 * k3 * k4 * kh
   Calculate required fictitious current: I'z = In / prod(ki)
   │
   ▼
4. Determine Minimum Cross-Section for Continuous Current (S_thermal):
   Find smallest standard cross-section S in {1.5 .. 300} mm² such that:
   I0(S, material, insulation, method, loaded_conductors) >= I'z
   │
   ▼
5. Check Voltage Drop Condition (S_voltage):
   Iterate upwards from S_thermal (if necessary) until:
   dU% = 100 * [b * (rho1 * L/S * cos_phi + lambda * L * sin_phi) * Ib] / U_ref <= dU_max
   │
   ▼
6. Check Short-Circuit Thermal Withstand (S_sc):
   If short-circuit parameters provided (Icc and t, or I²t):
   Verify S >= sqrt(I²t) / k. If not, increase S to smallest standard cross-section >= S_min.
   │
   ▼
7. Output Final Sizing:
   Selected Section S = max(S_thermal, S_voltage, S_sc)
   Effective Admissible Current Iz = I0(S) * prod(ki)
   Calculated dU (V and %)
   Calculated Thermal Stress Limit
```

---

## 9. Features Discovered & Normative Interfaces

### Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Operating Current | `calc_ib_single_phase` | Computes $I_b$ for 230V circuits from P(kW), S(kVA), or direct I(A) | $P$, $S$, or $I$; $V$ (default 230); $\cos\varphi$ (default 0.8) | $I_b$ (A) | Raise `ValueError` if $\cos\varphi \le 0$ or $> 1.0$, or $V \le 0$ | NF C 15-100 §311 |
| 2 | Operating Current | `calc_ib_three_phase` | Computes $I_b$ for 400V circuits from P(kW), S(kVA), or direct I(A) | $P$, $S$, or $I$; $U$ (default 400); $\cos\varphi$ (default 0.8) | $I_b$ (A) | Raise `ValueError` if $\cos\varphi \le 0$ or $> 1.0$, or $U \le 0$ | NF C 15-100 §311 |
| 3 | Harmonics | `calc_harmonic_factor` | Computes neutral current $I_N$ and derating factor $k_h$ per Table E.52.1 | $I_b$, third harmonic ratio $i_{h3}$ (0.0 to 1.0) | $k_h$, sizing basis (`phase` or `neutral`), $I_{\text{eff}}$ | Raise `ValueError` if $i_{h3} < 0$ | IEC 60364-5-52 Annex E |
| 4 | Derating Factors | `get_k1_installation` | Returns factor $k_1$ based on cable tray or conduit type | Installation code / tray type | $k_1 \in [0.95, 1.0]$ | Warn or fallback to 1.0 if unknown | UTE C 15-105 Table BD |
| 5 | Derating Factors | `get_k2_grouping` | Returns factor $k_2$ for $N$ grouped circuits / touching cables | Number of circuits $N \in [1, 20]$, method letter, spacing | $k_2 \in [0.38, 1.0]$ | Raise `ValueError` if $N < 1$; cap/extrapolate if $N > 20$ | NF C 15-100 Table 52N |
| 6 | Derating Factors | `get_k3_temperature` | Computes $k_3$ using normative square root formula or lookup table | Ambient temp $\theta$ (°C), insulation (`PVC` or `XLPE`) | $k_3$ factor | Raise `ValueError` if $\theta \ge \theta_{\max}$ (70°C for PVC, 90°C for XLPE) | NF C 15-100 Table 52K |
| 7 | Derating Factors | `get_k4_soil` | Returns $k_4$ for buried cables based on soil condition | Soil thermal resistivity or moisture type | $k_4 \in [0.70, 1.21]$ | Fallback to 1.0 (normal soil) | NF C 15-100 Table 52M |
| 8 | Reference Table | `lookup_i0` | Exact table lookup for reference admissible current $I_0$ | Section $S$, Conductor (`Cu`/`Al`), Insulation (`PVC`/`XLPE`), Method (`B`/`C`/`E`/`F`), Loaded conductors (2/3) | $I_0$ (A) | Raise `KeyError` if section not in standard series | NF C 15-100 Table 52H / UTE C 15-105 Table BD |
| 9 | Coordination | `select_protection_in` | Selects next standard protection rating $I_n \ge I_b$ | $I_b$ (A), protection series | $I_n$ (A) | Raise `ValueError` if $I_b > 630\text{ A}$ | NF C 15-100 §433.1 |
| 10 | Voltage Drop | `calc_voltage_drop` | Calculates exact absolute ($\Delta U$ in V) and relative ($\Delta U\%$) voltage drop | $I_b, L, S, \cos\varphi$, system type, conductor material | $\Delta U$ (V), $\Delta U\%$ (%) | Raise `ValueError` if $S \le 0$ or $L < 0$ | UTE C 15-105 §5.3 |
| 11 | Thermal Withstand | `check_thermal_stress` | Verifies adiabatic withstand $I^2 t \le k^2 S^2$ | $I^2 t$ (or $I_{cc}$ and $t$), $S$, conductor material, insulation | Pass/Fail, $S_{\min}$ (mm²) | Raise `ValueError` if clearing time $t > 5\text{ s}$ (non-adiabatic) | NF C 15-100 §434.5.2 |
| 12 | Cable Engine | `size_cable` | End-to-end cable sizing calculation returning optimal section | All circuit and environmental parameters | Complete sizing report object (S, $I_b, I_n, I_z, \Delta U$, factors) | Raise `SizingError` if no section up to 300 mm² satisfies constraints | UTE C 15-105 Chapter 5 |

---

## 10. Edge Cases and Constraint Boundaries

| # | Feature | Edge Case Input | Observed / Required Normative Behavior |
|---|---------|-----------------|----------------------------------------|
| 1 | Operating Current | $P = 0\text{ kW}$ or $I = 0\text{ A}$ | Reject with validation error ($I_b$ must be $> 0$). |
| 2 | Operating Current | $\cos\varphi = 1.0$ (purely resistive) | $\sin\varphi = 0$, reactance term drops out of voltage drop: $\Delta U = b \times \rho_1 \frac{L}{S} I_b$. |
| 3 | Operating Current | $\cos\varphi \le 0$ or $\cos\varphi > 1.0$ | Reject with validation error ($0 < \cos\varphi \le 1.0$). |
| 4 | Ambient Temperature | $\theta = 30^\circ\text{C}$ in air | $k_3 = 1.000$ exactly (baseline reference). |
| 5 | Ambient Temperature | $\theta \ge 70^\circ\text{C}$ for PVC | Disallowed! Ambient temp equals or exceeds max insulation operating temp. Engine must reject with an explicit descriptive error. |
| 6 | Ambient Temperature | $\theta \ge 90^\circ\text{C}$ for XLPE | Disallowed! Ambient temp equals or exceeds max XLPE operating temp. Engine must reject. |
| 7 | Grouping Factor | $N = 1$ circuit | $k_2 = 1.00$ exactly. |
| 8 | Grouping Factor | Spaced cables ($d \ge D$) | $k_2 = 1.00$ regardless of circuit count. |
| 9 | Harmonics | $i_{h3} = 0.15$ (15%) | $k_h = 1.00$, sized on phase current $I_b$. |
| 10 | Harmonics | $i_{h3} = 0.33$ (33%) | $k_h = 0.86$, sized on phase current $I_b$. Neutral conductor section equals phase. |
| 11 | Harmonics | $i_{h3} = 0.40$ (40%) | $k_h = 0.86$, sized on neutral current $I_N = 3 \times 0.40 \times I_b = 1.2 \times I_b$. |
| 12 | Voltage Drop | $S \le 16\text{ mm}^2$ | Linear reactance $\lambda$ can be set to $0$ per UTE C 15-105 §5.3 (pure resistive drop). |
| 13 | Voltage Drop | Very long run ($L > 200\text{ m}$) | Section selected for thermal capacity ($S_{\text{thermal}}$) violates $\Delta U \le \Delta U_{\max}$. Engine must auto-upsize to next standard sections until voltage drop passes. |
| 14 | Thermal Withstand | Fault clearing time $t > 5\text{ s}$ | Adiabatic equation $I^2 t \le k^2 S^2$ no longer applies (non-adiabatic regime). Warning or error must be emitted. |
| 15 | Material Sizing | Aluminium with $S < 16\text{ mm}^2$ | In French industrial standards, aluminium conductors are not permitted below $16\text{ mm}^2$ (or $10\text{ mm}^2$). Engine must enforce this minimum cross-section limit for Al. |

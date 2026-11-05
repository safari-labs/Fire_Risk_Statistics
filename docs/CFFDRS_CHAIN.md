# The CFFDRS chain as this study implements it, and where imagery can enter

Written 2026-11-05 at James's request: "these are very key points". The **where imagery can enter** section is the reference for every slot experiment and for P12.

Implementation is in `Fire_Risk_Model/src/data/`: `fwi.py` (Van Wagner 1987), `fbp.py` and `fbp_behaviour.py` (ST-X-3 1992 with the GLC-X-10 2009 updates), `ignition.py` (GLC-X-42 Table 1; Beverly & Wotton 2007). FWI and FBP are checked against the `cffdrs` R package to 1e-4 relative. The torch mirrors used by the networks are in `Fire_Risk_FW/src/fire_risk_fw/fbp_torch.py` and `ignition_torch.py`.

CFFDRS has no single "value". It rates three processes (GLC-X-42 p. 32, Table 1): ignition, spread, and consumption/intensity.

```
13:00 LDT weather (T, RH, wind, 24 h rain)
   │
   ├─ daily recursion ─► FFMC, DMC, DC        (moisture codes, carry yesterday's state)
   │                       ├─► ISI = f(FFMC, wind)       ─┐
   │                       ├─► BUI = f(DMC, DC)          ─┼─► FWI = f(ISI, BUI)
   │                       └──────────────► Ignition: class(FFMC), class(DMC), P(sustained flaming)
   │
   └─► FBP (+ fuel type, slope, aspect, lat/lon/elev/date, PC, PDF, curing, CBH, CFL)
          FMC → SFC → slope wind WSV → ISI_fbp → RSI → BE → ROS → CSI, RSO → CFB → CFC → TFC → HFI
```

## Where imagery can enter

Every other input in the chain is weather, terrain or the calendar. An imager can only inform the inputs below. Each is a **slot** (plan, "Processes × slots"), with four possible sources: `cffdrs` (operational), `imagery_replace` (an estimator's value through the unchanged equations), `imagery_correct` (a bounded learned correction), `ablated` (a fixed default).

| Slot | Enters the equations at | Process | Operational (cffdrs) source | Imagery estimate | Experiment | Status (2026-11-05) |
|---|---|---|---|---|---|---|
| **Fuel type** | Selects every row of the fuel table: a, b, c, BUI0, q, CBH, CFL, the SFC equation, the ignition category | All three | CWFIS FBP layer; SCANFI fuel tree | Ecology model family head (P6a) → fuel code | E-35 | Ready to launch |
| **Percent conifer (PC)** | M-1/M-2 mixtures of RSI, SFC, ISF and CFC | Spread, intensity | Layer code (M-1/2 C25/C50/C75); SCANFI species | Ecology model PC head | E-36, E-57 | AT RISK / SUPPORTED vs twin only |
| **Percent dead fir (PDF)** | M-3/M-4 mixtures of RSI and CFC | Spread, intensity | ST-X-3 default 35 % | None (no label) | T3 | Blocked |
| **Green-up (leaf state)** | D-1 vs D-2 (×0.2), M-2/M-4 deciduous share (×0.2); spring vs summer grass ignition category | Ignition, spread | CWFIS green-up product | S2 phenology date | E-40 | Not built |
| **Curing (CC)** | O-1 curing factor CF; GFMC | Ignition, spread | CWFIS NDVI curing (from 2024); FBP default 80 % | S2 NDVI / moisture | E-38 | PARTIAL, small n |
| **Crown base height (CBH)** | CSI, so RSO and crowning (CFB) | Intensity | ST-X-3 default by fuel type | Height head × ratio (ratio missing) | E-37 | AT RISK |
| **Foliar moisture (FMC)** | CSI; C-6 crown spread | Intensity | FBP eqs. 1–8 (date and place only) | LFMC retrieval | E-15, E-29, E-64 | No working retrieval (P6f) |
| **Canopy closure** | In-stand FFMC (Wotton & Beverly 2007) | Ignition | Fuel-type default closure | Ecology closure head | E-39 | Blocked on Q26 coefficients |
| **Snow-off / start-up date** | Day 1 of the FFMC/DMC/DC recursion; overwintered DC | All codes | 3 days after ERA5 snow-off, or 3 days ≥ 12 °C (Appendix C-2) | S2 NDSI snow-off per pixel | E-18, E-60 | REFUTED as an R0 gain; SWIR1 worth ~4 days |
| **Crown fuel load (CFL)** | CFC, so TFC and HFI | Intensity | ST-X-3 default by fuel type | None built (biomass would be the route) | — | Not registered |
| **Grass fuel load (GFL)** | O-1 SFC | Intensity | 0.35 kg/m² default | None built | — | Not registered |

Under A-41 SAFARI delivers the slow structure slots (fuel type, PC, closure, height → CBH). The fast slots (curing, green-up, snow-off, FMC) come from Sentinel-2/HLS or the issued CWFIS products, with SAFARI imagery for calibration and validation. A-49 weighs the four structure heads equally in the band decision.

Inputs imagery cannot reach: temperature, RH, wind, rain (the moisture codes and ISI), slope and aspect (from a DEM), latitude, longitude, elevation and date (FMC's equation). Weather age (E-20) and station density (G3) bound what any product can do, but are not imagery slots.

## 1. Inputs

| Input | Unit | Used by |
|---|---|---|
| T, 2 m air temperature at 13:00 LDT | °C | FFMC, DMC, DC |
| H, relative humidity | % (capped at 100) | FFMC, DMC |
| W, 10 m wind speed | km/h | FFMC, ISI, FBP |
| P, rain over the 24 h ending 13:00 | mm | FFMC, DMC, DC |
| Month | – | DMC and DC day-length factors |
| Fuel type, slope GS (%), aspect, wind direction | – | FBP |
| Lat, lon, elevation, day of year | – | FBP foliar moisture |
| PC, PDF, curing CC (%), grass fuel load GFL, CBH, CFL | – | FBP, by fuel type |

Start values on day 1: FFMC 85, DMC 6, DC 15. Season start (GLC-X-42 Appendix C-2): the third consecutive snow-free day after 1 March, or, where winter had no snow cover, the third consecutive day at or above 12 °C.

Overwintered DC (Lawson & Armitage 2008), a = b = 0.75, Pw the precipitation between fall and spring:

```
Qf = 800·exp(−DC_fall/400);   Qs = a·Qf + b·3.94·Pw;   DC_spring = max(400·ln(800/Qs), 15)
```

## 2. FWI System: the moisture codes (daily recursion)

**FFMC** (time lag about 2/3 day). The constant 147.2772 = 250·59.5/101.

```
m0 = 147.2772·(101 − F0)/(59.5 + F0)
rain, if P > 0.5 (rf = P − 0.5), both terms on the pre-rain m0:
  m0 += 42.5·rf·exp(−100/(251 − m0))·(1 − exp(−6.93/rf)) [+ 0.0015·(m0 − 150)²·√rf if m0 > 150];  m0 ≤ 250
Ed = 0.942·H^0.679 + 11·exp((H − 100)/10) + 0.18·(21.1 − T)·(1 − exp(−0.115·H))
Ew = 0.618·H^0.753 + 10·exp((H − 100)/10) + 0.18·(21.1 − T)·(1 − exp(−0.115·H))
drying (m0 > Ed):  k0 = 0.424·[1 − (H/100)^1.7] + 0.0694·√W·[1 − (H/100)^8]
                   kd = 0.581·k0·exp(0.0365·T);   m = Ed + (m0 − Ed)·10^(−kd)
wetting (m0 < Ew): kl = 0.424·[1 − ((100−H)/100)^1.7] + 0.0694·√W·[1 − ((100−H)/100)^8]
                   kw = 0.581·kl·exp(0.0365·T);   m = Ew − (Ew − m0)·10^(−kw)
otherwise m = m0
FFMC = 59.5·(250 − m)/(147.2772 + m), clipped to [0, 101]
```

**DMC** (time lag about 15 days):

```
rain, if P > 1.5:  re = 0.92·P − 1.27;   Mo = 20 + 280/exp(0.023·P0)
  b = 100/(0.5 + 0.3·P0) if P0 ≤ 33;  14 − 1.3·ln(P0) if P0 ≤ 65;  6.2·ln(P0) − 17.2 otherwise
  Mr = Mo + 1000·re/(48.77 + b·re);   P0 = max(43.43·(5.6348 − ln(Mr − 20)), 0)
drying: K = 1.894·(T + 1.1)·(100 − H)·Le·10⁻⁴ (0 if T ≤ −1.1);   DMC = max(P0 + K, 0)
Le (46 N, Jan–Dec): 6.5 7.5 9.0 12.8 13.9 13.9 12.4 10.9 9.4 8.0 7.0 6.0  (E-50: rescaled by latitude)
```

**DC** (time lag about 53 days):

```
rain, if P > 2.8:  rd = 0.83·P − 1.27;   Q0 = 800·exp(−D0/400);   Qr = Q0 + 3.937·rd
                   D0 = max(400·ln(800/Qr), 0)
drying: V = max(0.36·(T + 2.8) + Lf, 0)  (V = max(Lf, 0) if T ≤ −2.8);   DC = D0 + 0.5·V
Lf (Jan–Dec): −1.6 −1.6 −1.6 0.9 3.8 5.8 6.4 5.0 2.4 0.4 −1.6 −1.6
```

## 3. FWI System: the behaviour indices (same day)

```
ISI:  m = 147.2772·(101 − FFMC)/(59.5 + FFMC)
      f(W) = exp(0.05039·W);   f(F) = 91.9·exp(−0.1386·m)·(1 + m^5.31/4.93·10⁷)
      ISI = 0.208·f(W)·f(F)
BUI:  0.8·DMC·DC/(DMC + 0.4·DC)                                   if DMC ≤ 0.4·DC
      DMC − [1 − 0.8·DC/(DMC + 0.4·DC)]·(0.92 + (0.0114·DMC)^1.7) otherwise
FWI:  f(D) = 0.626·BUI^0.809 + 2 if BUI ≤ 80, else 1000/(25 + 108.64·exp(−0.023·BUI))
      B = 0.1·ISI·f(D);   FWI = exp(2.72·(0.434·ln B)^0.647) if B > 1, else B
```

DSR (0.0272·FWI^1.77) is not computed.

## 4. Ignition

Ordinal classes (GLC-X-42 Table 1):

| Class | Sustained flaming, from FFMC | Lightning ignition, from DMC |
|---|---|---|
| Low | 0–75 | 0–10 |
| Moderate | 76–84 | 11–25 |
| High | 85–89 | 26–45 |
| Very High | 90–92 | 46–60 |
| Extreme | ≥ 93 | ≥ 61 |

P(sustained flaming) from a small firebrand (Beverly & Wotton 2007, Table 6): P = 1/(1 + exp(−(b0 + Σ bi·xi))).

| Category | FBP fuel types (A-30) | b0 | Predictors |
|---|---|---|---|
| FC1 spring grass | O-1a/b before leaf flush | 7.3703 | −0.1725·RH |
| FC2 summer grass | O-1a/b after leaf flush | −23.3755 | 0.2895·FFMC |
| FC3 pine on lichen | C-1 (C-3/4 on lichen) | −34.8731 | 0.4304·FFMC |
| FC4 pine on moss | C-3, C-4 | −4.414 | 0.3368·FWI |
| FC5 pine needles | C-5, C-6, C-7 (analogue) | −4.8479 | 0.0258·DMC + 0.6032·ISI |
| FC6 mixedwood on moss | M-1 to M-4 | −24.3837 | 0.2407·FFMC + 0.0638·DMC |
| FC8 black spruce on moss | C-2 | −38.9 | 0.4117·FFMC + 0.0679·DMC |
| FC10 aspen leaf litter | D-1, D-2 | −4.1990 | 0.0421·DMC |

Slash has no category (NaN). Stage C's R0 is this P at the window's most common fuel code. In-stand FFMC by canopy closure (Wotton & Beverly 2007) and P(ignition | lightning stroke) by DMC (Wotton & Wheatley 2025) are coded but refuse to run until their coefficients arrive (Q26).

## 5. FBP System

**Foliar moisture (eqs. 1–8)**, longitude positive west:

```
no elevation:  LATN = 46 + 23.4·exp(−0.0360·(150 − LON));  D0 = round(151·LAT/LATN)
elevation:     LATN = 43 + 33.7·exp(−0.0351·(150 − LON));  D0 = round(142.1·LAT/LATN + 0.0172·ELV)
ND = |day − D0|;  FMC = 85 + 0.0189·ND² (ND < 30);  32.9 + 3.17·ND − 0.0288·ND² (ND < 50);  120
FMC = 0 for D-1, D-2, S-1 to S-3, O-1
```

**Surface fuel consumption SFC (kg/m²):**

| Fuel | SFC |
|---|---|
| C-1 | 0.75 ± 0.75·√(1 − exp(−0.23·\|FFMC − 84\|)), + if FFMC > 84 |
| C-2, M-3, M-4 | 5·(1 − exp(−0.0115·BUI)) |
| C-3, C-4 | 5·(1 − exp(−0.0164·BUI))^2.24 |
| C-5, C-6 | 5·(1 − exp(−0.0149·BUI))^2.48 |
| C-7 | 2·(1 − exp(−0.104·(FFMC − 70))) [FFMC > 70] + 1.5·(1 − exp(−0.0201·BUI)) |
| D-1, D-2 | 1.5·(1 − exp(−0.0183·BUI)) |
| M-1, M-2 | PC·SFC(C-2) + (1 − PC)·SFC(D-1) |
| O-1 | GFL (default 0.35) |
| S-1 | 4·(1 − exp(−0.025·BUI)) + 4·(1 − exp(−0.034·BUI)) |
| S-2 | 10·(1 − exp(−0.013·BUI)) + 6·(1 − exp(−0.060·BUI)) |
| S-3 | 12·(1 − exp(−0.0166·BUI)) + 20·(1 − exp(−0.0210·BUI)) |

**Slope folded into the wind (eqs. 39–51):**

```
SF  = exp(3.533·(GS/100)^1.2)   (10 if GS ≥ 70)
RSF = RSZ·SF        RSZ: ROS at ISI(FFMC, wind 0), no buildup effect
ISF = ln(1 − (RSF/a)^(1/c))/(−b)        (O-1: a·CF; mixed fuels blended as RSI)
WSE = ln(ISF/(0.208·f(F)))/0.05039;  above 40 km/h: 28 − ln(1 − ISF/(2.496·f(F)))/0.0818, cap 112.45
WSV = |W·(sin, cos)WAZ + WSE·(sin, cos)SAZ|;  RAZ = direction of that vector
```

**ISI with FBP's wind function**: f(W) = exp(0.05039·WSV) below 40 km/h, 12·(1 − exp(−0.0818·(WSV − 28))) above; ISI_fbp = 0.208·f(W)·f(F). It differs from the FWI System's ISI by the slope-adjusted wind and the bend above 40 km/h.

**Initial rate of spread RSI (m/min):**

```
basic fuels:  RSI = a·(1 − exp(−b·ISI))^c
M-1: PC·RSI(C-2) + (1 − PC)·RSI(D-1)        M-2: PC·RSI(C-2) + 0.2·(1 − PC)·RSI(D-1)
M-3: PDF·RSI(M-3) + (1 − PDF)·RSI(D-1)      M-4: PDF·RSI(M-4) + 0.2·(1 − PDF)·RSI(D-1)
D-2: 0.2·RSI(D-1)
O-1: RSI·CF,  CF = 0.005·(exp(0.061·CC) − 1) if CC < 58.8, else 0.176 + 0.02·(CC − 58.8)
```

**Buildup effect, spread, crowning, consumption, intensity:**

```
BE  = exp(50·ln(q)·(1/BUI − 1/BUI0));   ROS = BE·RSI
C-6: RSS = BE·30·(1 − exp(−0.08·ISI))³;  FME = 1000·(1.5 − 0.00275·FMC)⁴/(460 + 25.9·FMC)
     RSC = 60·(1 − exp(−0.0497·ISI))·FME/0.778;  ROS = RSS + CFB·(RSC − RSS)
CSI = 0.001·CBH^1.5·(460 + 25.9·FMC)^1.5          critical surface intensity, kW/m
RSO = CSI/(300·SFC)                               critical spread rate, m/min
CFB = 1 − exp(−0.23·(ROS − RSO)) if ROS > RSO, else 0
CFC = CFL·CFB  (×PC for M-1/M-2, ×PDF for M-3/M-4)
TFC = SFC + CFC;   HFI = 300·TFC·ROS (kW/m)
fire type: surface if CFB < 0.1, crown if CFB ≥ 0.9, otherwise intermittent crown
```

**Fuel constants (ST-X-3 Tables 6–8):**

| Fuel | a | b | c | BUI0 | q | CBH (m) | CFL (kg/m²) |
|---|---|---|---|---|---|---|---|
| C-1 | 90 | 0.0649 | 4.5 | 72 | 0.90 | 2 | 0.75 |
| C-2 | 110 | 0.0282 | 1.5 | 64 | 0.70 | 3 | 0.80 |
| C-3 | 110 | 0.0444 | 3.0 | 62 | 0.75 | 8 | 1.15 |
| C-4 | 110 | 0.0293 | 1.5 | 66 | 0.80 | 4 | 1.20 |
| C-5 | 30 | 0.0697 | 4.0 | 56 | 0.80 | 18 | 1.20 |
| C-6 | 30 | 0.0800 | 3.0 | 62 | 0.80 | 7 | 1.80 |
| C-7 | 45 | 0.0305 | 2.0 | 106 | 0.85 | 10 | 0.50 |
| D-1/D-2 | 30 | 0.0232 | 1.6 | 32 | 0.90 | – | – |
| M-1/M-2 | (C-2, D-1) | | | 50 | 0.80 | 6 | 0.80 |
| M-3 | 120 | 0.0572 | 1.4 | 50 | 0.80 | 6 | 0.80 |
| M-4 | 100 | 0.0404 | 1.48 | 50 | 0.80 | 6 | 0.80 |
| S-1 | 75 | 0.0297 | 1.3 | 38 | 0.75 | – | – |
| S-2 | 40 | 0.0438 | 1.7 | 63 | 0.75 | – | – |
| S-3 | 55 | 0.0829 | 3.2 | 31 | 0.75 | – | – |
| O-1a | 190 | 0.0310 | 1.4 | 1 | 1.0 | – | – |
| O-1b | 250 | 0.0350 | 1.7 | 1 | 1.0 | – | – |

Input handling follows `cffdrs`: out-of-range PC, PDF, CC and GFL revert to 50, 35, 80 and 0.35; CBH and CFL to the table; a supplied FMC outside (0, 120] falls back to the equation. FBP refuses FWI2025 codes (A-26).

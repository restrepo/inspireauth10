"""Names of the topics and areas kept for the tables of 2026-11-09: resolution 16, up to 20 Leiden
passes, seed 1 (the medoid of seeds 1-4), area resolution 0.3 (out/clusters/steady_r16_s1.npz).
Topic names were carried over by overlap from the first named run (names_r16.py) where a topic
shares at least 60% of its papers both ways with one old topic, and written again for the 9 that
did not. Topic numbers are those of cluster.py (largest first); a rerun renumbers them."""
AREAS = {
    0: 'Particle physics: experiment, phenomenology, QCD and hadrons',
    1: 'Theory: strings, fields, gravity and cosmology',
    2: 'Astrophysics and gravitational waves',
    3: 'Quantum physics: information, optics and condensed matter',
    4: 'Nuclear structure and reactions',
    5: 'Accelerator physics',
}
TOPICS = [
    'Accelerator physics and beam dynamics',  # 0
    'Quantum computing algorithms',  # 1
    'Laser-plasma and advanced accelerators',  # 2
    'Nuclear structure and gamma spectroscopy',  # 3
    'Nuclear reactions and the optical model',  # 4
    'Neutrino oscillations',  # 5
    'LHC experiments and the Higgs discovery',  # 6
    'Stars, exoplanets and stellar catalogues',  # 7
    'Nuclear masses, fission and coupled channels',  # 8
    'Silicon trackers and LHC detector upgrades',  # 9
    'Ultra-high-energy cosmic rays and air showers',  # 10
    'Quantum cryptography',  # 11
    'Multiparticle production in hadron collisions',  # 12
    'Regge theory and the S-matrix',  # 13
    'Gaseous detectors',  # 14
    'Bell nonlocality and quantum foundations',  # 15
    'Nucleon-nucleon potentials and nuclear forces',  # 16
    'Quark flavour physics and the CKM matrix',  # 17
    'Dark energy and observational cosmology',  # 18
    'Transport models of heavy-ion collisions',  # 19
    'Lattice QCD: fermions and algorithms',  # 20
    'Gamma-ray astronomy and blazars',  # 21
    'Entanglement theory',  # 22
    'Topological insulators and Majorana modes',  # 23
    'Supermassive black holes and AGN',  # 24
    'Muon colliders and neutrino factories',  # 25
    'Confinement, renormalization group and statistical field theory',  # 26
    'Galactic astronomy and the distance scale',  # 27
    'Ultracold atoms and Rydberg physics',  # 28
    'Decoherence and interpretations of quantum mechanics',  # 29
    'Geant4 and detector simulation',  # 30
    'Dark matter evidence and direct detection',  # 31
    'Supersymmetric gauge theories and dualities',  # 32
    'Quark-gluon plasma at RHIC',  # 33
    'LEP-era e+e- physics and event generators',  # 34
    'Nuclear equation of state and isospin physics',  # 35
    'Exotic hadrons and meson spectroscopy',  # 36
    'Interstellar dust and infrared astronomy',  # 37
    'Gamma-ray bursts',  # 38
    'Open quantum systems',  # 39
    'Galaxy clusters and X-ray cosmology',  # 40
    'X-ray binaries and black-hole accretion',  # 41
    'Continuous-variable quantum information',  # 42
    'Hadron models and meson exchange',  # 43
    'Supersymmetric quantum mechanics and mathematical physics',  # 44
    'Baryon resonances and photoproduction',  # 45
    'Gravitational-wave detectors and detections',  # 46
    'Superconducting qubits and circuit QED',  # 47
    'Noncommutative geometry and field theory',  # 48
    'Nuclear astrophysics and nucleosynthesis',  # 49
    'Quark models and hadron spectroscopy',  # 50
    'AdS/CFT correspondence',  # 51
    'Cosmic microwave background',  # 52
    'Photonic quantum computing and entangled photons',  # 53
    'Neutrino astronomy and statistical methods',  # 54
    'Neutron stars and binary neutron-star mergers',  # 55
    'Integrable models and exact S-matrices',  # 56
    'Deep inelastic scattering and parton evolution',  # 57
    'Neutrinoless double-beta decay',  # 58
    'Superstring theory foundations',  # 59
    'QCD phase transition, NJL model and chiral magnetic effect',  # 60
    'Cosmic-ray positrons and antimatter',  # 61
    'Quantum channels and resource theories',  # 62
    'Halo nuclei and nuclear radii',  # 63
    'Top quark and parton distributions at the Tevatron',  # 64
    'Atomic mass evaluation',  # 65
    'Matrix models and 2D quantum gravity',  # 66
    'Nuclear density functional theory',  # 67
    'Quantum thermalization, chaos and localization',  # 68
    'Loop quantum gravity',  # 69
    'Kaon physics and CP violation',  # 70
    'Kerr black holes and black-hole imaging',  # 71
    'Holographic entanglement entropy',  # 72
    'Foundations of electroweak theory',  # 73
    'Neutrino mass models and lepton flavour violation',  # 74
    'Higher-dimensional black holes',  # 75
    'Classical tests of general relativity',  # 76
    'BFKL and small-x QCD',  # 77
    'Nuclear data: level densities and neutron reactions',  # 78
    'Casimir effect',  # 79
    'Two-dimensional conformal field theory',  # 80
    'Long-baseline neutrino experiments',  # 81
    'Geometric phases and quantum control',  # 82
    'F-theory and topological strings',  # 83
    'Current algebra and early QCD',  # 84
    'Heavy ions at the LHC and quarkonium suppression',  # 85
    'Cosmological simulations and structure formation',  # 86
    'Axions and the strong CP problem',  # 87
    'Quantization and renormalization of gauge theories',  # 88
    'Plasma astrophysics: turbulence and reconnection',  # 89
    'Strongly correlated electrons and graphene',  # 90
    'Heavy-quark decays and HQET',  # 91
    'Proton radius and nucleon form factors',  # 92
    'Galaxy dynamics and stellar disks',  # 93
    'Quantum error correction',  # 94
    'Multiloop calculations and computer algebra',  # 95
    'Lorentz and CPT violation',  # 96
    'Quantum sensing and NV centres',  # 97
    'Strong-field QED',  # 98
    'Teleparallel and metric-affine gravity',  # 99
    'Effective and higher-derivative quantum gravity',  # 100
    'B physics at LHCb and Belle II',  # 101
    'Black-hole perturbations and quasinormal modes',  # 102
    'Particle acceleration at astrophysical shocks',  # 103
    'Large-scale structure and galaxy surveys',  # 104
    'Charmonium and the J/psi',  # 105
    'Electroweak symmetry breaking and oblique corrections',  # 106
    'Quantum networks and repeaters',  # 107
    'Black-hole thermodynamics',  # 108
    'Automated one-loop calculations and Higgs decays',  # 109
    'Confinement and gauge-field topology',  # 110
    'Magnetars and neutron-star physics',  # 111
    'NLO QCD for jets and PDFs at the LHC',  # 112
    'Chern-Simons theory and the quantum Hall effect',  # 113
    'Topological order and generalized symmetries',  # 114
    'Cavity optomechanics and quantum noise',  # 115
    'Quark and lepton mass matrices and flavour symmetries',  # 116
    'Thermal and nonequilibrium field theory',  # 117
    'Light-matter interaction and photonic quantum technologies',  # 118
    'Spin structure of the nucleon',  # 119
    'Non-Hermitian and PT-symmetric physics',  # 120
    'Magnetic monopoles and solitons',  # 121
    'Pulsars',  # 122
    'Supersymmetry at colliders',  # 123
    'Inflationary cosmology',  # 124
    'String dualities, D-branes and M-theory',  # 125
    'W and Z discovery and hadron-collider physics of the 1980s',  # 126
    'Star-forming and infrared galaxies',  # 127
    'Quantum metrology',  # 128
    'Astrometry, time series and Gaia',  # 129
    'Electric dipole moments and atomic tests',  # 130
    'Stellar population synthesis and galaxy evolution',  # 131
    'Solar composition and stellar opacities',  # 132
    'Hadrons in dense matter and dileptons',  # 133
    'Dyson-Schwinger equations and QCD Green functions',  # 134
    'Large-N QCD and Skyrmions',  # 135
    'Chiral symmetry and quark masses',  # 136
    'Cosmological models and inhomogeneities',  # 137
    'Quantum groups and Lie superalgebras',  # 138
    '21-cm cosmology and reionization',  # 139
    'Foundations of supersymmetry',  # 140
    'Extra dimensions and braneworlds',  # 141
    'Integrability in AdS/CFT',  # 142
    'Gravitational instantons and differential geometry',  # 143
    'Vortices, cosmic strings and topological defects',  # 144
    'Mathematical general relativity and algebraic QFT',  # 145
    'Foundations of quantum field theory',  # 146
    'TMD factorization and transverse-momentum resummation',  # 147
    'Instantons and anomalies',  # 148
    'Machine learning in particle physics',  # 149
    'Superconducting RF cavities',  # 150
    'QCD sum rules',  # 151
    'Perturbative QCD and asymptotic freedom',  # 152
    'Muon g-2',  # 153
    'Planck cosmology and parameter inference',  # 154
    'Driven-dissipative many-body systems',  # 155
    'Quantum annealing and adiabatic computation',  # 156
    'Particle dark matter candidates and relic abundance',  # 157
    'Spin qubits in quantum dots',  # 158
    'Dark matter halos',  # 159
    'Aharonov-Bohm effect and topological defects in quantum mechanics',  # 160
    'Generalized parton distributions and the EIC',  # 161
    'Quarkonium and potential models',  # 162
    'Weak interactions in nuclear beta decay',  # 163
    'Starburst galaxies and HII regions',  # 164
    'Electroweak precision and future e+e- colliders',  # 165
    'Pions in nuclei',  # 166
    'Supernova neutrinos and core collapse',  # 167
    'Supersymmetric model building',  # 168
    'Dark photons and hidden sectors',  # 169
    'X-ray instrumentation and Galactic HI',  # 170
    'Supergravity and Kaluza-Klein reductions',  # 171
    'Canonical quantum gravity and quantum cosmology',  # 172
    'Modified gravity and Horndeski theories',  # 173
    'Hawking radiation and minimal length',  # 174
    'f(R) gravity',  # 175
    'Post-Newtonian theory and the effective one-body approach',  # 176
    'Benchmarking and characterization of quantum devices',  # 177
    'Future cosmological surveys',  # 178
    'Nambu-Jona-Lasinio model and the chiral magnetic effect',  # 179
    'f(R,T) gravity and relativistic stars',  # 180
    'Regularization and the axial anomaly',  # 181
    'Black-hole accretion and jets',  # 182
    'Gravitational radiation theory and asymptotic charges',  # 183
    'Quantum teleportation and measurement-based computing',  # 184
    'Primordial magnetic fields',  # 185
    'Fast radio bursts and pulsar emission',  # 186
    'Quantum walks and state transfer',  # 187
    'Astropy and multiwavelength surveys',  # 188
    'Hypernuclei and hyperon-nucleon interactions',  # 189
    'Large extra dimensions',  # 190
    'Tensor networks and DMRG',  # 191
    'Compact-binary populations',  # 192
    'Quantum Brownian motion and fields in de Sitter space',  # 193
    'Wormholes and global spacetime structure',  # 194
    'Quantum fields in curved spacetime',  # 195
    'Antimatter and precision tests in traps',  # 196
    'Cosmological perturbations and non-Gaussianity',  # 197
    'Nuclear structure functions and the EMC effect',  # 198
    'Type Ia supernovae and white dwarfs',  # 199
    'Perturbative QCD tools and multiple interactions',  # 200
    'Dark matter evidence and MOND',  # 201
    'Tunnelling times and relativistic foundations',  # 202
    'Primordial black holes',  # 203
    'Conformal bootstrap and RG flows',  # 204
    'String field theory and tachyons',  # 205
    'Big Bang nucleosynthesis',  # 206
    'Trapped ions and quantum simulation',  # 207
    'String landscape and swampland',  # 208
    'Reheating and freeze-in dark matter',  # 209
    'Higher-spin theories',  # 210
    'Domain walls and cosmological phase transitions',  # 211
    'Astrophysical plasma codes and the baryon budget',  # 212
    'Black-hole microstates and fuzzballs',  # 213
    'Uncertainty principle and quantum measurement',  # 214
    'Kaon-nucleon interactions and the Lambda(1405)',  # 215
    'Gravitational lensing',  # 216
    'Electroweak baryogenesis and sphalerons',  # 217
    'Two-photon physics',  # 218
    'Emergent gravity and nonextensive statistics',  # 219
    'Numerical relativity of binary black holes',  # 220
    'Standard Model effective field theory',  # 221
    'Light-front QCD',  # 222
    'Exclusive processes in perturbative QCD',  # 223
    'Space-based gravitational-wave detectors',  # 224
    'Relativistic hydrodynamics and viscosity',  # 225
    'SYK model and bounds on chaos',  # 226
    'Coherent elastic neutrino-nucleus scattering',  # 227
    'BESIII and tau-charm physics',  # 228
    'Two-Higgs-doublet models',  # 229
    'Radio surveys',  # 230
    'Relativistic quark models',  # 231
    'Pulsar timing arrays and supermassive black-hole binaries',  # 232
    'Cosmological singularities and accretion',  # 233
    'Scalar-tensor theories and the dilaton',  # 234
    'Baryon-antibaryon and meson resonances',  # 235
    'False vacuum decay',  # 236
    'Chiral perturbation theory',  # 237
    'Composite Higgs',  # 238
    'Parity violation and early QED',  # 239
    'Three-dimensional gravity and BTZ black holes',  # 240
    'Quantum Zeno effect and dissipative dynamics',  # 241
    'Gravitational collapse and critical phenomena',  # 242
    'Ultralight dark matter and boson stars',  # 243
    'Multi-messenger neutron-star mergers and kilonovae',  # 244
    'Sterile neutrinos and neutrino cosmology',  # 245
    'Scattering amplitudes and the double copy',  # 246
    'Group contractions and kinematical symmetries',  # 247
    'First stars and high-redshift quasars',  # 248
    'Density functional theory and electronic structure',  # 249
    'Ekpyrotic and pre-big-bang cosmology',  # 250
    'Baryogenesis and leptogenesis',  # 251
    'Analogue gravity',  # 252
    "Z' bosons and E6 models",  # 253
    'Kaluza-Klein theories',  # 254
    'Random matrix theory and the Dirac spectrum',  # 255
    'R-parity violation and leptoquarks',  # 256
    'Global PDF fits',  # 257
    'Channeling and charged particles in matter',  # 258
    'Heavy and doubly charmed baryons',  # 259
    'Higgs vacuum stability',  # 260
    'Gravitational microlensing',  # 261
    'Quantum simulation of lattice gauge theories',  # 262
    'Lattice QCD at finite density',  # 263
    'Structured light and electron vortex beams',  # 264
    'Tidal disruption events and infrared surveys',  # 265
    'Geometric mechanics and covariant field theory',  # 266
    'Causal sets and the cosmological constant',  # 267
    'Measurement-induced phase transitions',  # 268
    'Tests of general relativity and scalar-tensor gravity',  # 269
    'Scientific software for data analysis',  # 270
    'Kibble-Zurek dynamics and quantum quenches',  # 271
    'Horava-Lifshitz gravity',  # 272
    'Two-dimensional dilaton gravity',  # 273
    'Left-right symmetric models',  # 274
    'Supersymmetric Yang-Mills and deconfinement',  # 275
    'Superconductivity and the origins of the Higgs mechanism',  # 276
    'Quantum games',  # 277
    'Quantum field theory of neutrino oscillations',  # 278
    'Photon mass limits and fractional charges',  # 279
    'Knot invariants and Chern-Simons theory',  # 280
    'Chaos and quantum reservoir computing',  # 281
    'Localization of gravitational energy',  # 282
    'Fourth generation of fermions',  # 283
    'The 511 keV line and MeV dark matter',  # 284
    'Positivity bounds and causality',  # 285
    'Exact solutions of the Einstein-Maxwell equations',  # 286
    'Landau-Yang theorem and diphoton resonances',  # 287
    'Quantum image processing',  # 288
    'Diffuse infrared background and data analysis',  # 289
    'TTbar deformations',  # 290
    'Sloan Digital Sky Survey',  # 291
    'Quantum entanglement at colliders',  # 292
    'Unparticle physics',  # 293
    'Black holes as graviton condensates',  # 294
    'Statistics and fitting in particle physics',  # 295
    'Varying nuclear decay rates',  # 296
    'Miscellaneous: astronomy data systems',  # 297
    'SSC detector proposals',  # 298
    'Z-pinch and pulsed-power accelerators',  # 299
    'Miscellaneous: Planck parameters and exotic smoothness',  # 300
    'Miscellaneous: accelerator facilities and history',  # 301
    'Statistical sampling and fitting software',  # 302
    'Scalar-field cosmology and statistical systems',  # 303
]
assert len(TOPICS) == 304

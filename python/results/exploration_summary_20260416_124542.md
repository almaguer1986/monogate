# Exploration Session Summary

**Started:** 20260416_124542  |  **Ended:** 20260416_133805

## Overall Results

| Metric | Value |
|--------|-------|
| Phases completed | 5 / 5 |
| Total conjectures tested | 5200 |
| Successfully proved | 106 (2%) |
| Reached MCTS tier | 0 (0.0%) |
| Novel discoveries | 106 |
| Scorer buffer (final) | 0 samples |
| Scorer trained | False |
| Total runtime | 3143s (52.4 min) |

## Signal Interpretation

- **Prove rate 2%**: Too hard — lower temperature
- **MCTS rate 0.0%**: No MCTS reach — everything solved by SymPy/numerical (consider higher temperature)

## Per-Phase Breakdown

| Phase | Seed | Temp | Rounds | Generated | Proved | MCTS | Discoveries | Time |
|-------|------|------|--------|-----------|--------|------|-------------|------|
| trig_medium | trig | 0.7 | 100 | 2000 | 20 | 0 | 20 | 229s |
| trig_high | trig | 0.9 | 50 | 1000 | 26 | 0 | 26 | 143s |
| exp_medium | exponential | 0.7 | 50 | 1000 | 20 | 0 | 20 | 1032s |
| special_medium | special | 0.8 | 30 | 600 | 20 | 0 | 20 | 755s |
| physics_medium | physics | 0.7 | 30 | 600 | 20 | 0 | 20 | 984s |

## Discoveries (106 total)

1. `cos(-(2*x)) == cos((2*x))`  [exact]
2. `cos(-(x/2)) == cos((x/2))`  [exact]
3. `cos(-(x+1)) == cos((x+1))`  [exact]
4. `cos(-(3*x)) == cos((3*x))`  [exact]
5. `sin(-(2*x)) == -sin((2*x))`  [exact]
6. `sin(-(x/2)) == -sin((x/2))`  [exact]
7. `sin(-(x+1)) == -sin((x+1))`  [exact]
8. `sin(-(3*x)) == -sin((3*x))`  [exact]
9. `(-(cos(-x))) == (-(cos(x)))`  [exact]
10. `(-(sin(-x))) == (-(-sin(x)))`  [exact]
11. `(2*(cos(-x))) == (2*(cos(x)))`  [exact]
12. `((cos(-x))/2) == ((cos(x))/2)`  [exact]
13. `(3*(cos(-x))) == (3*(cos(x)))`  [exact]
14. `(2*(sin(-x))) == (2*(-sin(x)))`  [exact]
15. `((sin(-x))/2) == ((-sin(x))/2)`  [exact]
16. `(3*(sin(-x))) == (3*(-sin(x)))`  [exact]
17. `sin((2*x))**2 + cos((2*x))**2 == 1`  [exact]
18. `sin((x/2))**2 + cos((x/2))**2 == 1`  [exact]
19. `sin((x+1))**2 + cos((x+1))**2 == 1`  [exact]
20. `sin((3*x))**2 + cos((3*x))**2 == 1`  [exact]
21. `cos(-(2*x)) == cos((2*x))`  [exact]
22. `cos(-(x/2)) == cos((x/2))`  [exact]
23. `cos(-(x+1)) == cos((x+1))`  [exact]
24. `cos(-(3*x)) == cos((3*x))`  [exact]
25. `sin(-(2*x)) == -sin((2*x))`  [exact]
26. `sin(-(x/2)) == -sin((x/2))`  [exact]
27. `sin(-(x+1)) == -sin((x+1))`  [exact]
28. `sin(-(3*x)) == -sin((3*x))`  [exact]
29. `(-(cos(-x))) == (-(cos(x)))`  [exact]
30. `(-(sin(-x))) == (-(-sin(x)))`  [exact]
31. `(2*(cos(-x))) == (2*(cos(x)))`  [exact]
32. `((cos(-x))/2) == ((cos(x))/2)`  [exact]
33. `(3*(cos(-x))) == (3*(cos(x)))`  [exact]
34. `(2*(sin(-x))) == (2*(-sin(x)))`  [exact]
35. `((sin(-x))/2) == ((-sin(x))/2)`  [exact]
36. `(3*(sin(-x))) == (3*(-sin(x)))`  [exact]
37. `cos(-(x+-0.25)) == cos((x+-0.25))`  [exact]
38. `sin(-(x+-0.25)) == -sin((x+-0.25))`  [exact]
39. `sin((2*x))**2 + cos((2*x))**2 == 1`  [exact]
40. `sin((x/2))**2 + cos((x/2))**2 == 1`  [exact]
41. `cos(-(x+-0.1)) == cos((x+-0.1))`  [exact]
42. `sin(-(x+0.25)) == -sin((x+0.25))`  [exact]
43. `sin(-(x+-0.1)) == -sin((x+-0.1))`  [exact]
44. `cos(-(x+0.1)) == cos((x+0.1))`  [exact]
45. `cos(-(x+0.25)) == cos((x+0.25))`  [exact]
46. `sin(-(x+0.1)) == -sin((x+0.1))`  [exact]
47. `(-(exp(0))) == (-(1))`  [exact]
48. `(-(log(1))) == (-(0))`  [exact]
49. `(2*(exp(0))) == (2*(1))`  [exact]
50. `((exp(0))/2) == ((1)/2)`  [exact]
51. `(3*(exp(0))) == (3*(1))`  [exact]
52. `(2*(log(1))) == (2*(0))`  [exact]
53. `((log(1))/2) == ((0)/2)`  [exact]
54. `(3*(log(1))) == (3*(0))`  [exact]
55. `(-(exp(log(x)))) == (-(x))`  [exact]
56. `(-(log(exp(x)))) == (-(x))`  [numerical]
57. `log(1/(x+1)) == -log((x+1))`  [numerical]
58. `log(1/(2*x)) == -log((2*x))`  [numerical]
59. `log(1/(x/2)) == -log((x/2))`  [numerical]
60. `log(1/(3*x)) == -log((3*x))`  [numerical]
61. `(2*(exp(log(x)))) == (2*(x))`  [exact]
62. `((exp(log(x)))/2) == ((x)/2)`  [exact]
63. `(3*(exp(log(x)))) == (3*(x))`  [exact]
64. `((log(exp(x)))/2) == ((x)/2)`  [numerical]
65. `(2*(log(exp(x)))) == (2*(x))`  [numerical]
66. `(3*(log(exp(x)))) == (3*(x))`  [numerical]
67. `(-(erf(0))) == (-(0))`  [exact]
68. `(-(cos(0))) == (-(1))`  [exact]
69. `(2*(erf(0))) == (2*(0))`  [exact]
70. `((erf(0))/2) == ((0)/2)`  [exact]
71. `(3*(erf(0))) == (3*(0))`  [exact]
72. `(2*(cos(0))) == (2*(1))`  [exact]
73. `((cos(0))/2) == ((1)/2)`  [exact]
74. `(3*(cos(0))) == (3*(1))`  [exact]
75. `erf((2*x)) == -erf(-(2*x))`  [exact]
76. `erf((x/2)) == -erf(-(x/2))`  [exact]
77. `erf((x+1)) == -erf(-(x+1))`  [exact]
78. `erf((3*x)) == -erf(-(3*x))`  [exact]
79. `(-(erf(x))) == (-(-erf(-x)))`  [exact]
80. `erf((2*x)) + erf(-(2*x)) == 0`  [exact]
81. `erf((x/2)) + erf(-(x/2)) == 0`  [exact]
82. `erf((x+1)) + erf(-(x+1)) == 0`  [exact]
83. `erf((3*x)) + erf(-(3*x)) == 0`  [exact]
84. `erf((2*x)) + erfc((2*x)) == 1`  [numerical]
85. `erf((x/2)) + erfc((x/2)) == 1`  [numerical]
86. `erf((x+1)) + erfc((x+1)) == 1`  [numerical]
87. `cos((2*x)) == cos(-(2*x))`  [exact]
88. `cos((x/2)) == cos(-(x/2))`  [exact]
89. `cos((x+1)) == cos(-(x+1))`  [exact]
90. `cos((3*x)) == cos(-(3*x))`  [exact]
91. `(-(cos(x))) == (-(cos(-x)))`  [exact]
92. `(2*(cos(x))) == (2*(cos(-x)))`  [exact]
93. `((cos(x))/2) == ((cos(-x))/2)`  [exact]
94. `(3*(cos(x))) == (3*(cos(-x)))`  [exact]
95. `cos((2*x))**2 + sin((2*x))**2 == 1`  [exact]
96. `cos((x/2))**2 + sin((x/2))**2 == 1`  [exact]
97. `cos((x+1))**2 + sin((x+1))**2 == 1`  [exact]
98. `cos((3*x))**2 + sin((3*x))**2 == 1`  [exact]
99. `(-(exp(-1/x) / exp(-1/x))) == (-(1))`  [exact]
100. `(-(cos(x)**2 + sin(x)**2)) == (-(1))`  [exact]
101. `1/cosh((2*x))**2 == 1/cosh(-(2*x))**2`  [exact]
102. `1/cosh((x/2))**2 == 1/cosh(-(x/2))**2`  [exact]
103. `1/cosh((x+1))**2 == 1/cosh(-(x+1))**2`  [exact]
104. `1/cosh((3*x))**2 == 1/cosh(-(3*x))**2`  [exact]
105. `(-(exp(-x**2))) == (-(exp(-(-x)**2)))`  [exact]
106. `(2*(exp(-1/x) / exp(-1/x))) == (2*(1))`  [exact]

## Files

- Full data: `results\exploration\exploration_20260416_124542.json`
- Discoveries: `results\exploration\discoveries_20260416_124542.json`
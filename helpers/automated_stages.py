# Old order
# [F_Eth_outValve, F_N2O_outValve, F_Eth_ventValve, F_N2O_ventValve, F_N20_pValve, G_N2_inValve G_N2O_inValve, G_N2_ventValve, G_N2O_ventValve]

# New order
# [Ox pressure, Oxvent, Ethvent, Oxout, Ethout, GS Ox in, GS N2 in, GS n2 vent, GSox vent]


# Keys for stages
stages_keys = ['1.1', '1.2', '1.3', '2.1', '2.2', '2.3', '3.1', '3.2', '3.3', '4.1', '4.2', '4.3', '5', '6']

fuelling_stages = {
    '1.1': [180, 180, 180, 180, 180, 180, 180, 180, 180],
    '1.2': [180, 180, 180, 0, 0, 180, 180, 180, 180],
    '1.3': [180, 180, 180, 180, 180, 180, 180, 180, 180],
    '2.1': [180, 180, 180, 180, 180, 180, 180, 180, 180],
    '2.2': [180, 180, 180, 180, 0, 180, 180, 180, 180],
    '2.3': [180, 180, 180, 180, 180, 180, 180, 180, 180],
    '3.1': [180, 180, 0, 180, 180, 180, 180, 180, 180],
    '3.2': [180, 0, 0, 180, 180, 180, 180, 180, 180],
    '3.3': [180, 180, 180, 180, 180, 180, 180, 180, 180],
    '4.1': [0, 180, 180, 180, 180, 180, 180, 180, 180],
    '4.2': [180, 180, 180, 180, 180, 180, 180, 180, 180],
    '4.3': [180, 180, 180, 180, 0, 180, 180, 180, 180],
    '5': [180, 180, 180, 180, 180, 180, 180, 180, 180],
    '6': [180, 180, 180, 0, 180, 0, 180, 180, 180],
    'E-stop': [0, 0, 180, 0, 180, 0, 0, 180, 180]
}


# Initial example for reference

# # Notations for valves
# # [G_N2O_inValve, G_N2O_ventValve, G_N2_inValve, G_N2_ventValve]

# # Keys for stages
# stages_keys = ['1.1', '1.2', '1.3', '2.1', '2.2', '2.3', '2.4', '3.1', '3.2', '3.3', '4', '5']

# fuelling_stages = {
#     '1.1': [0, 0, 0, 0],
#     '1.2': [1, 1, 1, 1],
#     '1.3': [1, 1, 1, 1],
#     '2.1': [1, 1, 1, 1],
#     '2.2': [180, 1, 1, 1],
#     '2.3': [180, 1, 1, 1],
#     '2.4': [1, 180, 1, 1],
#     '3.1': [1, 180, 180, 1],
#     '3.2': [1, 180, 1, 180],
#     '3.3': [1, 180, 1, 180],
#     '4': [1, 180, 1, 180],
#     '5': [1, 180, 1, 180],
#     'E-stop': [1, 180, 1, 180]
# }

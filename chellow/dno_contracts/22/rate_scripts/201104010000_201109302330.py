def lafs():
    return {
        'lv-net': {
            'winter-weekday-peak': 1.087,
            'winter-weekday-day': 1.080,
            'night': 1.072,
            'other': 1.075},
        'lv-sub': {
            'winter-weekday-peak': 1.078,
            'winter-weekday-day': 1.072,
            'night': 1.065,
            'other': 1.068},
        'hv-net': {
            'winter-weekday-peak': 1.065,
            'winter-weekday-day': 1.058,
            'night': 1.046,
            'other': 1.051}}


def tariffs():
    return {
        '510': {
            'description': 'High Voltage HH Metered',
            'gbp-per-mpan-per-day': 0.6485,
            'gbp-per-kva-per-day': 0.017,
            'excess-gbp-per-kva-per-day': 0.017,
            'red-gbp-per-kwh': 0.16342,
            'amber-gbp-per-kwh': 0.0004,
            'green-gbp-per-kwh': 0.00058,
            'gbp-per-kvarh': 0.00238},
        '520': {
            'description': 'High Voltage HH Metered',
            'gbp-per-mpan-per-day': 0.6485,
            'gbp-per-kva-per-day': 0.017,
            'excess-gbp-per-kva-per-day': 0.017,
            'red-gbp-per-kwh': 0.16342,
            'amber-gbp-per-kwh': 0.0004,
            'green-gbp-per-kwh': 0.00058,
            'gbp-per-kvarh': 0.00238},
        '521': {
            'description': 'HV Generation Intermittent',
            'gbp-per-mpan-per-day': 0.2666,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.04470,
            'amber-gbp-per-kwh': -0.00059,
            'green-gbp-per-kwh': -0.00063,
            'gbp-per-kvarh': 0.00086},
        '522': {
            'description': 'High Voltage Sub HH Metered',
            'gbp-per-mpan-per-day': 0.6485,
            'gbp-per-kva-per-day': 0.0117,
            'excess-gbp-per-kva-per-day': 0.0117,
            'red-gbp-per-kwh': 0.13824,
            'amber-gbp-per-kwh': 0.00014,
            'green-gbp-per-kwh': 0.00041,
            'gbp-per-kvarh': 0.00187},
        '523': {
            'description': 'HV Sub Generation Intermittent',
            'gbp-per-mpan-per-day': 0.2666,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.04181,
            'amber-gbp-per-kwh': -0.00042,
            'green-gbp-per-kwh': -0.00055,
            'gbp-per-kvarh': 0.00064},
        '524': {
            'description': 'HV Generation Non-Intermittent',
            'gbp-per-mpan-per-day': 0.2666,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.04470,
            'amber-gbp-per-kwh': -0.00059,
            'green-gbp-per-kwh': -0.00063,
            'gbp-per-kvarh': 0.00086},
        '525': {
            'description': 'HV Sub Generation Non-Intermittent',
            'gbp-per-mpan-per-day': 0.2666,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.04181,
            'amber-gbp-per-kwh': -0.00042,
            'green-gbp-per-kwh': -0.00055,
            'gbp-per-kvarh': 0.00064},
        '526': {
            'description': 'LV Sub Generation Non-Intermittent',
            'gbp-per-mpan-per-day': 0.00,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.06204,
            'amber-gbp-per-kwh': -0.00181,
            'green-gbp-per-kwh': -0.00117,
            'gbp-per-kvarh': 0.00118},
        '527': {
            'description': 'LV Generation Non-Intermittent',
            'gbp-per-kva-per-day': 0.00,
            'gbp-per-mpan-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.06632,
            'amber-gbp-per-kwh': -0.00214,
            'green-gbp-per-kwh': -0.00132,
            'gbp-per-kvarh': 0.00136},
        '540': {
            'description': 'Low Voltage Sub HH Metered',
            'gbp-per-mpan-per-day': 0.0554,
            'gbp-per-kva-per-day': 0.0228,
            'excess-gbp-per-kva-per-day': 0.0228,
            'red-gbp-per-kwh': 0.19431,
            'amber-gbp-per-kwh': 0.00115,
            'green-gbp-per-kwh': 0.00097,
            'gbp-per-kvarh': 0.00297},
        '550': {
            'description': 'Low Voltage Sub HH Metered',
            'gbp-per-mpan-per-day': 0.0554,
            'gbp-per-kva-per-day': 0.0228,
            'excess-gbp-per-kva-per-day': 0.0228,
            'red-gbp-per-kwh': 0.19431,
            'amber-gbp-per-kwh': 0.00115,
            'green-gbp-per-kwh': 0.00097,
            'gbp-per-kvarh': 0.00297},
        '551': {
            'description': 'LV Sub Generation Intermittent',
            'gbp-per-mpan-per-day': 0.00,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.06204,
            'amber-gbp-per-kwh': -0.00181,
            'green-gbp-per-kwh': -0.00117,
            'gbp-per-kvarh': 0.00118},
        '570': {
            'description': 'Low Voltage HH Metered',
            'gbp-per-mpan-per-day': 0.0756,
            'gbp-per-kva-per-day': 0.0211,
            'excess-gbp-per-kva-per-day': 0.0211,
            'red-gbp-per-kwh': 0.21381,
            'amber-gbp-per-kwh': 0.00205,
            'green-gbp-per-kwh': 0.00138,
            'gbp-per-kvarh': 0.00353},
        '580': {
            'description': 'Low Voltage HH Metered',
            'gbp-per-mpan-per-day': 0.0756,
            'gbp-per-kva-per-day': 0.0211,
            'excess-gbp-per-kva-per-day': 0.0211,
            'red-gbp-per-kwh': 0.21381,
            'amber-gbp-per-kwh': 0.00205,
            'green-gbp-per-kwh': 0.00138,
            'gbp-per-kvarh': 0.00353},
        '581': {
            'description': 'LV Generation Intermittent',
            'gbp-per-mpan-per-day': 0.00,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.06632,
            'amber-gbp-per-kwh': -0.00214,
            'green-gbp-per-kwh': -0.00132,
            'gbp-per-kvarh': 0.00136}}

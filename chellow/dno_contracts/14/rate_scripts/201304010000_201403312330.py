def lafs():
    return {
        'lv-net': {
            'night': 1.052,
            'winter-weekday-peak': 1.077,
            'winter-weekday-day': 1.069,
            'other': 1.060},
        'lv-sub': {
            'night': 1.052,
            'winter-weekday-peak': 1.077,
            'winter-weekday-day': 1.069,
            'other': 1.060},
        'hv-net': {
            'night': 1.031,
            'winter-weekday-peak': 1.044,
            'winter-weekday-day': 1.041,
            'other': 1.035}}


def tariffs():
    return {
        '127': {
            'description': 'LV',
            'gbp-per-mpan-per-day': 0.1042,
            'gbp-per-kva-per-day': 0.0322,
            'excess-gbp-per-kva-per-day': 0.0322,
            'red-gbp-per-kwh': 0.08705,
            'amber-gbp-per-kwh': 0.00627,
            'green-gbp-per-kwh': 0.00056,
            'gbp-per-kvarh': 0.00332},
        '129': {
            'description': 'LV',
            'gbp-per-mpan-per-day': 0.1042,
            'gbp-per-kva-per-day': 0.0322,
            'excess-gbp-per-kva-per-day': 0.0322,
            'red-gbp-per-kwh': 0.08705,
            'amber-gbp-per-kwh': 0.00627,
            'green-gbp-per-kwh': 0.00056,
            'gbp-per-kvarh': 0.00332},
        '128': {
            'description': 'LV Sub',
            'gbp-per-mpan-per-day': 0.1042,
            'gbp-per-kva-per-day': 0.0421,
            'excess-gbp-per-kva-per-day': 0.0421,
            'red-gbp-per-kwh': 0.07452,
            'amber-gbp-per-kwh': 0.00481,
            'green-gbp-per-kwh': 0.00034,
            'gbp-per-kvarh': 0.00267},
        '365': {
            'description': 'HV',
            'gbp-per-mpan-per-day': 1.0475,
            'gbp-per-kva-per-day': 0.0495,
            'excess-gbp-per-kva-per-day': 0.0495,
            'red-gbp-per-kwh': 0.05298,
            'amber-gbp-per-kwh': 0.00292,
            'green-gbp-per-kwh': 0.00017,
            'gbp-per-kvarh': 0.00171},
        '367': {
            'description': 'HV',
            'gbp-per-mpan-per-day': 1.0475,
            'gbp-per-kva-per-day': 0.0495,
            'excess-gbp-per-kva-per-day': 0.0495,
            'red-gbp-per-kwh': 0.05298,
            'amber-gbp-per-kwh': 0.00292,
            'green-gbp-per-kwh': 0.00017,
            'gbp-per-kvarh': 0.00171},
        '625': {
            'description': 'LV Generation NHH',
            'gbp-per-mpan-per-day': 0,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.00702,
            'amber-gbp-per-kwh': -0.00702,
            'green-gbp-per-kwh': -0.0702,
            'gbp-per-kvarh': 0},
        '570': {
            'description': 'LV Sub Generation NHH',
            'gbp-per-mpan-per-day': 0,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.00592,
            'amber-gbp-per-kwh': -0.00592,
            'green-gbp-per-kwh': -0.00592,
            'gbp-per-kvarh': 0},
        '571': {
            'description': 'LV Generation Intermittent',
            'gbp-per-mpan-per-day': 0,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.00702,
            'amber-gbp-per-kwh': -0.00702,
            'green-gbp-per-kwh': -0.00702,
            'gbp-per-kvarh': -0.00279},
        '573': {
            'description': 'LV Generation Non-Intermittent',
            'gbp-per-mpan-per-day': 0,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.05482,
            'amber-gbp-per-kwh': -0.00563,
            'green-gbp-per-kwh': -0.0006,
            'gbp-per-kvarh': -0.00279},
        '572': {
            'description': 'LV Sub Generation Intermittent',
            'gbp-per-mpan-per-day': 0,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.00592,
            'amber-gbp-per-kwh': -0.00592,
            'green-gbp-per-kwh': -0.00592,
            'gbp-per-kvarh': -0.00251},
        '574': {
            'description': 'LV Sub Generation Non-Intermittent',
            'gbp-per-mpan-per-day': 0,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.04661,
            'amber-gbp-per-kwh': -0.00471,
            'green-gbp-per-kwh': -0.00047,
            'gbp-per-kvarh': -0.00251},
        '575': {
            'description': 'HV Generation Intermittent',
            'gbp-per-mpan-per-day': -0.1798,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.0592,
            'amber-gbp-per-kwh': -0.0592,
            'green-gbp-per-kwh': -0.0592,
            'gbp-per-kvarh': -0.0206},
        '577': {
            'description': 'HV Generation Non-Intermittent',
            'gbp-per-mpan-per-day': -0.1798,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.03135,
            'amber-gbp-per-kwh': -0.00298,
            'green-gbp-per-kwh': -0.00022,
            'gbp-per-kvarh': -0.00206}}

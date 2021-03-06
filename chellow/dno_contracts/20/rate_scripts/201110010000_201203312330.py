def lafs():
    return {
        'lv-net': {
            'peak': 1.089,
            'winter-weekday': 1.085,
            'other': 1.078,
            'night': 1.074},
        'lv-sub': {
            'peak': 1.061,
            'winter-weekday': 1.059,
            'other': 1.056,
            'night': 1.057},
        'hv-net': {
            'peak': 1.042,
            'winter-weekday': 1.040,
            'other': 1.035,
            'night': 1.029},
        'hv-sub': {
            'peak': 1.021,
            'winter-weekday': 1.020,
            'other': 1.018,
            'night': 1.017}}


def tariffs():
    return {
        '001,477,909': {
            'description': 'LV Generation Intermittent',
            'gbp-per-mpan-per-day': 0.00,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.00670,
            'amber-gbp-per-kwh': -0.00670,
            'green-gbp-per-kwh': -0.00670,
            'gbp-per-kvarh': 0.00191},
        '002': {
            'description': 'LV Generation Non-Intermittent',
            'gbp-per-mpan-per-day': 0.00,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.04460,
            'amber-gbp-per-kwh': -0.00906,
            'green-gbp-per-kwh': -0.00144,
            'gbp-per-kvarh': 0.00191},
        '003': {
            'description': 'LV Sub Generation Intermittent',
            'gbp-per-mpan-per-day': 0.00,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.00583,
            'amber-gbp-per-kwh': -0.00583,
            'green-gbp-per-kwh': -0.00583,
            'gbp-per-kvarh': 0.00177},
        '004': {
            'description': 'LV Sub Generation Non-Intermittent',
            'gbp-per-mpan-per-day': 0.00,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.04017,
            'amber-gbp-per-kwh': -0.00759,
            'green-gbp-per-kwh': -0.00121,
            'gbp-per-kvarh': 0.00177},
        '005': {
            'description': 'HV Generation Intermittent',
            'gbp-per-mpan-per-day': 0.9811,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.00349,
            'amber-gbp-per-kwh': -0.00349,
            'green-gbp-per-kwh': -0.00349,
            'gbp-per-kvarh': 0.00151},
        '006,478,910': {
            'description': 'HV Generation Non-Intermittent',
            'gbp-per-mpan-per-day': 0.9811,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.02865,
            'amber-gbp-per-kwh': -0.00360,
            'green-gbp-per-kwh': -0.00059,
            'gbp-per-kvarh': 0.00151},
        '007': {
            'description': 'HV Sub Generation Intermittent',
            'gbp-per-mpan-per-day': 0.9811,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.00271,
            'amber-gbp-per-kwh': -0.00271,
            'green-gbp-per-kwh': -0.00271,
            'gbp-per-kvarh': 0.00073},
        '008': {
            'description': 'HV Sub Generation Non Intermittent',
            'gbp-per-mpan-per-day': 0.9811,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.02341,
            'amber-gbp-per-kwh': -0.00261,
            'green-gbp-per-kwh': -0.00041,
            'gbp-per-kvarh': 0.00073},
        '401,475': {
            'description': 'LV Medium Non Domestic',
            'gbp-per-mpan-per-day': 0.2157,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': 0.01744,
            'amber-gbp-per-kwh': 0.0092,
            'green-gbp-per-kwh': 0.000,
            'gbp-per-kvarh': 0.00},
        '453,470': {
            'description': 'LV HH Metered',
            'gbp-per-mpan-per-day': 0.0826,
            'gbp-per-kva-per-day': 0.0229,
            'excess-gbp-per-kva-per-day': 0.0229,
            'red-gbp-per-kwh': 0.07022,
            'amber-gbp-per-kwh': 0.00924,
            'green-gbp-per-kwh': 0.00161,
            'gbp-per-kvarh': 0.00267},
        '455': {
            'description': 'LVS HH Metered',
            'gbp-per-mpan-per-day': 0.0325,
            'gbp-per-kva-per-day': 0.0432,
            'excess-gbp-per-kva-per-day': 0.0432,
            'red-gbp-per-kwh': 0.05691,
            'amber-gbp-per-kwh': 0.00530,
            'green-gbp-per-kwh': 0.001,
            'gbp-per-kvarh': 0.00199},
        '658,476': {
            'description': 'HV HH Metered',
            'gbp-per-mpan-per-day': 0.7921,
            'gbp-per-kva-per-day': 0.0484,
            'excess-gbp-per-kva-per-day': 0.0484,
            'red-gbp-per-kwh': 0.04664,
            'amber-gbp-per-kwh': 0.00367,
            'green-gbp-per-kwh': 0.00069,
            'gbp-per-kvarh': 0.00143},
        '660': {
            'description': 'HVS HH Metered',
            'gbp-per-mpan-per-day': 1.3319,
            'gbp-per-kva-per-day': 0.0306,
            'excess-gbp-per-kva-per-day': 0.0306,
            'red-gbp-per-kwh': 0.04368,
            'amber-gbp-per-kwh': 0.00288,
            'green-gbp-per-kwh': 0.00054,
            'gbp-per-kvarh': 0.00120}}

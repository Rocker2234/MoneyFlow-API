def hdfc_grouper(txn_desc: str) -> str:
    grp_nm = ''
    if txn_desc.startswith('POS'):
        grp_nm = f"POS-{txn_desc[19:]}"
        if grp_nm == "POS-ZOMATOLIMITED":
            grp_nm = "POS-ZOMATO"
    elif txn_desc.startswith('UPI'):
        if txn_desc.startswith('UPI-AXIS-CRED.CLUB'):
            grp_nm = "UPI-AXIS-CRED.CLUB"
        else:  # Main Conversion
            grp_nm = txn_desc[:txn_desc.find("-", 4)]
        if txn_desc.startswith('UPI-IRCTC'):
            grp_nm = "UPI-IRCTC"
    elif txn_desc.startswith('IMPS'):
        temp = txn_desc.split('-')
        grp_nm = "-".join([temp[0], temp[2], temp[3], temp[4]])
    elif txn_desc.startswith('NEFT'):
        temp = txn_desc.split('-')
        grp_nm = "-".join([temp[0], temp[2]])
    elif txn_desc.startswith('ACH'):
        if txn_desc.startswith('ACHD-HDFCMF'):
            grp_nm = "MF - INVESTMENT"
        elif txn_desc.startswith("ACHC-SAL-IMSHLTHANALYSERP"):
            grp_nm = "SALARY CREDIT IQVIA"
    elif txn_desc.find("RAZPBSEINDIACOM") != -1:
        grp_nm = "MF - INVESTMENT"
    elif txn_desc.find("RDINSTALLMENT") != -1:
        grp_nm = "RDINSTALLMENT"
    elif txn_desc.find('-TPT-') != -1:
        grp_nm = txn_desc.split('-')[-1]
    return grp_nm

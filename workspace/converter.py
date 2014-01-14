# -*- coding: utf-8 -*-
import logging
import optparse
import sys
import os
import re
import codecs
from entity import comunidad, cuota, piso, user, cuotaCollection

LOGGING_LEVELS = {'critical': logging.CRITICAL,
                  'error': logging.ERROR,
                  'warning': logging.WARNING,
                  'info': logging.INFO,
                  'debug': logging.DEBUG}

RESULT = {
    "comunidad": None,
    "pisos": [],
    "cuotas": [],
    "personas": []
}

LINENUM = 0

CUOTAS = [(1,1), (2,11), (3,2), (4,8), (5, 5),
          (6,9), (7,7), (8,8), (9,9), (10,10),
          (11,11), (12,12)]

LOGGER = None
VIA_PATTERN = re.compile("^(C/|AVDA[.]?|PZA[.]?|PZ[.]?)\s")
PISO_PORTAL_PATTERN_1 = re.compile("(\d+)\s*-\s*(\d+.*)")
PISO_PORTAL_PATTERN_2 = re.compile("N*\s+(\d+)\s+(\d+.*)")
PISO_PORTAL_PATTERN_3 = re.compile("N*\s+(\d+)\s+(ATICO|BAJO)\s*")
PISO_PORTAL_PATTERN_4 = re.compile("(\d+\s+BIS)\s+(-)\s*")
PISO_PORTAL_PATTERN_5 = re.compile("(\d+\s+BIS)\s+(\d+.*)\s*")
PISO_PORTAL_PATTERN_6 = re.compile("(\d+)\s*-(.*)\s*$")
LOCAL_PATTERN = re.compile("LOCAL")
GARAJE_PATTERN  = re.compile("GARAJE")
GENERIC_CUOTA_ANUAL_PATTERN = re.compile("CUOTA ANUAL\s+[a-zA-Z0-9\(\)/]*\s+\d+[.\d,]*\s*$")
GENERIC_CUOTA_TRIMESTRAL_PATTERN = re.compile("CUOTA TRIMESTRAL\s+[a-zA-Z0-9\(\)]*\s+\d+[.\d,]*\s*$")
COMUNIDAD_CUOTA_PATTERN = re.compile("CUOTA COMUNIDAD\s+\d+[.\d,]*\s*$")
CUOTA_EXTRA_PATTERN = re.compile("CUOTA EXTRA")
CUOTA_PATTERN = re.compile("\s\d+[.\d,]*\s*$")

def userData_handler5380(line):
    """docstring for comunidad"""
    LOGGER.debug("%s", line)
    RESULT["comunidad"].parse(line)
    LOGGER.info("New comunidad!: %s\n", RESULT["comunidad"].nombre)

def userData_handler5680(line):
    """
    New user register
    5680H31927627001000000004903BIURRUN ETXERA, IÑAKITX                 2054000042000062905100000090000005990000000004 SEPTIEMBRE-11
    5680H31886872000000000009704ASURMENDI FERNANDEZ, JESUS MARIA        3008007310151731601200000062090006540000000086 CUOTA MENSUAL 62,09
    """
    LOGGER.debug("%s", line)
    persona = user.User()
    comu = RESULT["comunidad"]

    # Calculate numcomu and numprop format
    numcomuStr = str(RESULT["comunidad"].numcomu)
    #numcomu = RESULT["comunidad"].numcomu

    # numprop contains numcomu
    numpro = line[22:28].strip()
    numproIndex = numpro.index(numcomuStr)
    #persona.numprop = int(line[24:28])
    persona.numprop = int(numpro[numproIndex + len(numcomuStr):])
    #numpropTmp = int(numpro[numproIndex + len(numcomuStr):])
    #if divmod(numpropTmp, 100)[0] == 0:
        # id not bigger than 100
        # 9723 -> 9723
    #    persona.numprop = int(line[24:28])
    #else:
        # id bigger than 100
        # 97123 -> 9823
    #    persona.numprop = numcomu * 100 + numpropTmp

    persona.nombre = line[28:68].strip()
    persona.banco = line[68:72]
    persona.sucursal = line[72:76]
    persona.dccuenta = line[76:78]
    persona.numcta = line[78:88]

    RESULT["personas"].append(persona)
    cuotas = cuotaCollection.CuotaCollection()
    RESULT["cuotas"].append(cuotas)

    cuotas.numprop = persona.numprop
#######
#    if (cuotas.numprop == 14):
#        import pdb 
#        pdb.set_trace()
##########
    data = line[28:].strip()


    m = CUOTA_PATTERN.search(data)
    if m:
        cuoObject = {
                "titcuota": 0,
                "ptsrec": float(str(m.group(0).strip()).translate(None, ".").replace(",", "."))
                }

        if (GENERIC_CUOTA_TRIMESTRAL_PATTERN.search(data)):
            # 5680 associated to numcuota = 4, titcuota = 8
            cuoObject["titcuota"] = 8
            cuotas.cuotas[4] = cuoObject
        elif (GENERIC_CUOTA_ANUAL_PATTERN.search(data)):
            # 5680 associated to numcuota = 2, titcuota = 11
            cuoObject["titcuota"] = 11
            cuotas.cuotas[2] = cuoObject
        else:
            # 5680 associated to numcuota = 1, titcuota = 1
            cuoObject["titcuota"] = 1
            cuotas.cuotas[1] = cuoObject


    LOGGER.info("New propietario!: %2d: %s\n", persona.numprop,
                persona.nombre.encode("latin1"))

def userData_handler5681(line):
    """
    docstring for userDataHandler5681
    CUOTA ANUAL LOCAL
    CUOTA ANUAL GARAJE
    CUOTA ANUAL 
    """
    LOGGER.debug("%s", line)
    persona = RESULT["personas"][-1]
    cuotas = RESULT["cuotas"][-1]
    #cuotas.numprop = int(line[24:28])
    cuoObject = {
            "titcuota": 0,
            "ptsrec": 0.0
            }

    if LOCAL_PATTERN.search(line[28:]):
        # 5681 associated to numcuota = 3, titcuota = 2
        cuoObject["titcuota"] = 2
        cuotas.cuotas[3] = cuoObject
    elif (GARAJE_PATTERN.search(line[28:]) or 
          GENERIC_CUOTA_ANUAL_PATTERN.search(line[28:])):
        # 5681 associated to numcuota = 2, titcuota = 11
        cuoObject["titcuota"] = 11
        cuotas.cuotas[2] = cuoObject
    elif COMUNIDAD_CUOTA_PATTERN.search(line[28:]):
        # 5681 associated to numcuota = 1, titcuota = 1
        cuoObject["titcuota"] = 1
        cuotas.cuotas[1] = cuoObject
    else:
        assert False, ("register 5681 is neither a LOCAL nor GARAJE "
        "nor CUOTA ANUAL not CUOTA COMUNIDAD")

    data = line[28:].strip()
    m = CUOTA_PATTERN.search(data)
    if not m:
        assert False, "Unknow cuota number on register 5681"

    cuoObject["ptsrec"] = float(str(m.group(0).strip()).translate(None, ".").replace(",", "."))

def userData_handler5682(line):
    """docstring for userDataHandler5682"""
    LOGGER.debug("%s", line)
    cuotas = RESULT["cuotas"][-1]

    #import pdb
    #pdb.set_trace()
    #cuotas.numprop = int(line[24:28])

    cuoObject = {
            "titcuota": 0,
            "ptsrec": 0.0
            }

    # Check there is extra,
    # in this case, we are adding one cuota register to RESULT["cuotas"]
    # otherwise, associate to numcuota=1 unless it was already assigned
    if LOCAL_PATTERN.search(line[28:]):
        # 5681 associated to numcuota = 3, titcuota = 2
        cuoObject["titcuota"] = 2
        cuotas.cuotas[3] = cuoObject
    elif (CUOTA_EXTRA_PATTERN.search(line[28:]) or
            GENERIC_CUOTA_TRIMESTRAL_PATTERN.search(line[28:])):
        # 5682 associated to numcuota = 4, titcuota = 8
        cuoObject["titcuota"] = 8
        cuotas.cuotas[4] = cuoObject
    elif (GARAJE_PATTERN.search(line[28:]) or 
          GENERIC_CUOTA_ANUAL_PATTERN.search(line[28:])):
        # 5682 associated to numcuota = 2, titcuota = 11
        cuoObject["titcuota"] = 11
        cuotas.cuotas[2] = cuoObject
    else:
        # 5682 associated to numcuota = 1, titcuota = 1
        cuoObject["titcuota"] = 1
        cuotas.cuotas[1] = cuoObject

    data = line[28:].strip()
    m = CUOTA_PATTERN.search(data)
    if not m:
        assert False, "Unknow cuota number on register 5682"

    cuoObject["ptsrec"] = float(str(m.group(0).strip()).translate(None, ".").replace(",", "."))

def userData_handler5683(line):
    """
    New user register
    5683H31346026001000000002265 CUOTA ANUAL TRASTERO(13)         60,10
    """
    LOGGER.debug("%s", line)
    cuotas = RESULT["cuotas"][-1]

    # 5683 associated to numcuota = ?
    if 4 in cuotas.cuotas:
        # There is a previous cuota like this, forget
        LOGGER.debug("forgetting cuota: %s", line)
        return

    #cuotas.numprop = int(line[24:28])
    # 5683 associated to numcuota = 4, titcuota = 8
    cuoObject = {
            "titcuota": 8,
            "ptsrec": 0.0
            }
    cuotas.cuotas[4] = cuoObject
    data = line[28:].strip()
    m = CUOTA_PATTERN.search(data)
    if not m:
        assert False, "Unknow cuota number on register 5683"

    cuoObject["ptsrec"] = float(str(m.group(0).strip()).translate(None, ".").replace(",", "."))

def userData_handler5684(line):
    """
    docstring for userDataHandler5684
    """
    LOGGER.debug("%s", line)
    cuotas = RESULT["cuotas"][-1]

    cuoObject = {
            "titcuota": 0,
            "ptsrec": 0.0
            }

    # 5684 associated to numcuota = 3, titcuota = 2
    cuoObject["titcuota"] = 2
    cuotas.cuotas[3] = cuoObject

    data = line[28:].strip()
    m = CUOTA_PATTERN.search(data)
    if not m:
        assert False, "Unknow cuota number on register 5684"

    cuoObject["ptsrec"] = float(str(m.group(0).strip()).translate(None, ".").replace(",", "."))

def userData_handler5685(line):
    """docstring for userDataHandler5685"""
    LOGGER.debug("%s", line)


def userData_handler5686(line):
    """
    docstring for userDataHandler5686
    It is known cuota type (garaje, local, vecino)
    """
    LOGGER.debug("%s", line)
    cuotas = RESULT["cuotas"][-1]

    persona = RESULT["personas"][-1]

    # Via 
    m = None
    m = VIA_PATTERN.search(line[68:74])
    if m:
        # only first 2 chars will be written to output file
        persona.via = line[68:71].strip()
        viaIndex = 68 + len(m.group(1))
        persona.calle = line[viaIndex:108].strip()
    else:
        # default via: C/
        persona.via = "C/"
        persona.calle = line[68:108].strip()
        LOGGER.debug("calle def:  %s", persona.calle)

    # only 
    persona.pobla = line[108:116].strip()
    persona.cpostal = int(line[143:148])

    pis_obj = piso.Piso()
    pis_obj.numprop = persona.numprop
    pis_obj.numasocia = persona.numprop

    # Pattern matching depending on cuota type
    m = None
    
    # VECINO
    m_1 = PISO_PORTAL_PATTERN_1.search(persona.calle)
    m_2 = PISO_PORTAL_PATTERN_2.search(persona.calle)
    m_3 = PISO_PORTAL_PATTERN_3.search(persona.calle)
    m_4 = PISO_PORTAL_PATTERN_4.search(persona.calle)
    m_5 = PISO_PORTAL_PATTERN_5.search(persona.calle)
    m_6 = PISO_PORTAL_PATTERN_6.search(persona.calle)
    if m_1:
        m = m_1
    elif m_2:
        m = m_2
    elif m_3:
        m = m_3
    elif m_4:
        m = m_4
    elif m_5:
        m = m_5
    elif m_6:
        m = m_6

    if m:
        persona.piso = m.group(2).strip()
        persona.numcalle = m.group(1)
        persona.calle = persona.calle[:m.start()].strip().strip(".").strip()
        pis_obj.piso = persona.piso
    elif 1 not in cuotas.cuotas:
        # EXCEPTION
        # TRASTERO, LOCAL or GARAJE
        persona.piso = persona.calle
        persona.numcalle = "0"
        pis_obj.piso = persona.piso
    else:
        LOGGER.warning("Cannot parse VECINO at register 5686: %s",
                       persona.calle)
        persona.piso = persona.calle
        persona.numcalle = "0"
        pis_obj.piso = persona.piso

    # append piso
    RESULT["pisos"].append(pis_obj)

def end_of_file(line):
    """docstring for end_of_file"""
    LOGGER.debug("%s", line)
    numcomu = RESULT["comunidad"].numcomu

    for persona in RESULT["personas"]:
        persona.numcomu = numcomu
    for pisos in RESULT["pisos"]:
        pisos.numcomu = numcomu
        pisos.nfinca = numcomu
    for cuotas in RESULT["cuotas"]:
        cuotas.numcomu = numcomu

def feed(line):
    LOGGER.debug("%s", line)
    fields = line.split(",")
    assert len(fields) == 10, "line format not known"

    global LINENUM

    if LINENUM == 0:
        return

    # data structures
    cuotas = cuotaCollection.CuotaCollection()
    pis_obj = piso.Piso()
    user = user.User()

    # Format
    # CODE, NAME, BANKUETXEA, SUKURTSALA, DC, KONTUA, KUOTA, EMPTY, HELBIDEA, DESKRIBAPENA
    # 0000789108,MIKEL ETXEA,0000,0000,00,0000000000,70.00,,1ºDCHA,CUOTA MENSUAL COMUNID
    #

    # Users
    user.numcomu = RESULT["comunidad"].numcomu
    user.numprop = LINENUM + 1
    user.nombre = fields[1]
    user.banco = fields[2]
    user.sucursal = fields[3]
    user.dccuenta = fields[4]
    user.numcta = fields[5]
    user.piso = "0"
    user.numcalle = "0"
    user.calle = ""
    user.via = ""
    user.pobla = ""
    user.cpostal = ""

    # Pis_obj
    pis_obj.numcomu = user.numcomu
    pis_obj.numprop = user.numprop
    pis_obj.numasocia = user.numprop
    pis_obj.piso = user.piso
    pis_obj.nfinca = user.numcomu

    # Cuotas
    cuotas.numcomu = numcomu
    cuotas.impresu = 0
    cuotas.numprop = user.numprop

    titcuota = X
    indexCuota = X
    ptsrec = Y

    cuoObject = {
            "titcuota": titcuota,
            "ptsrec": ptsrec
            }
    cuotas.cuotas[indexCuota] = cuoObject

    RESULT["personas"].append(user)
    RESULT["pisos"].append(pis_obj)
    RESULT["cuotas"].append(cuotas)

    LINENUM += 1

def convert(filename, file_dir, encoding="latin1"):
    """docstring for splitter"""
    file_object = codecs.open(filename, mode = 'r', encoding = encoding)
    for line in file_object.readlines():
        feed(line)

    # Write files
    # Pisos
    out_file = open(os.path.join(file_dir, "WPISOS.TXT"), 'w')
    for entity in sorted ( RESULT["pisos"], key=lambda x: x.numprop ):
        entity.write(out_file)
        out_file.write("\n")
    out_file.close()
    LOGGER.info("WPISOS.TXT created!")

    # Cuotas
    # Now, a register 5680 may have more than one type of cuotas
    # Cuota.py object should remain simple
    # Generate WCUOTAS filling more than one CUOTA (numcuota, titcuota)
    out_file = open(os.path.join(file_dir, "WCUOTAS.TXT"), 'w')
    for cuotas in sorted ( RESULT["cuotas"], key=lambda x: x.numprop ):
        cuotasArray = []
        for c_index_numcuota, c_index_titcuota in CUOTAS:
            cuo = cuota.Cuota()
            cuo.numcomu = cuotas.numcomu
            cuo.numprop = cuotas.numprop
            cuo.impresu = cuotas.impresu

            # if there is in cuotas dict, then create cuota object with that info
            if c_index_numcuota in cuotas.cuotas:
                cuo.numcuota = c_index_numcuota
                assert c_index_titcuota == cuotas.cuotas[c_index_numcuota]["titcuota"], "titcuota do not match: [%d, %d]" % (c_index_titcuota, cuotas.cuotas[c_index_numcuota]["titcuota"])
                cuo.titcuota = c_index_titcuota
                cuo.ptsrec = cuotas.cuotas[c_index_numcuota]["ptsrec"]
                cuotasArray.append(cuo)
            else:
                cuo.numcuota = c_index_numcuota
                cuo.titcuota = c_index_titcuota
                cuo.ptsrec = 0
                cuotasArray.append(cuo)

        for cuo in cuotasArray:
            cuo.write(out_file)
            out_file.write("\n")

    out_file.close()
    LOGGER.info("WCUOTAS.TXT created!")

    # Personas
    out_file = open(os.path.join(file_dir, "WPERSONA.TXT"), 'w')
    for entity in sorted ( RESULT["personas"], key=lambda x: x.numprop ):
        entity.write(out_file)
        out_file.write("\n")
    out_file.close()
    LOGGER.info("WPERSONA.TXT created!")
    LOGGER.info("OUTPUT_DIR: %s" % (file_dir))
    LOGGER.info("Finished OK. YUHUUU!")

def main():
    parser = optparse.OptionParser()
    parser.add_option('-l', '--logging-level', help='Logging level')
    parser.add_option('-e', '--encoding', help='file encoding', default="latin1")
    parser.add_option('-o', '--output', help='output dir')
    (options, args) = parser.parse_args()

    assert len(args) == 2, "missin input params, check doc"

    logging_level = LOGGING_LEVELS.get(options.logging_level, logging.NOTSET)
    logging.basicConfig(level=logging_level,
                        format='%(asctime)-15s %(levelname)s: %(message)s')

    global LOGGER
    LOGGER = logging.getLogger()

    output_dir = os.path.abspath(options.output)
    if not os.path.exists( output_dir ):
        os.makedirs( output_dir )

    filename = args[0] 

    # comunidad
    RESULT["comunidad"] = comunidad.Comunidad()
    RESULT["comunidad"].numcomu = int(args[1]);

    #Input parameter parsing logic
    LOGGER.info(("Starting job pid: %s "
                 "filename: %s\n"),
                str(os.getpid()),
                filename)
    try:
        convert(filename, output_dir, options.encoding)
    except:
        from sys import exc_info
        from traceback import format_tb
        e_type, e_value, tb = exc_info()
        traceback = ['Unexpected fatal error: Traceback (most recent call last):']
        traceback += format_tb(tb)
        traceback.append('%s: %s' % (e_type.__name__, e_value))
        LOGGER.error("Unexpected error:  %s" % (traceback))
        LOGGER.info("Finished with errors. ARGHHHH!")

if __name__ == "__main__":
    main()

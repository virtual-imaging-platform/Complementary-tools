#!/bin/bash
set -o errexit -o noclobber -o nounset

USAGE="Usage: $0 <vo> <storage host>"

if [ $# -ne 2 ]
then
    echo "$USAGE" >&2
    exit 1
fi

if [ -z "${LCG_GFAL_INFOSYS:-}" ]; then
    echo "Environment variable LCG_GFAL_INFOSYS must be set." >&2
    exit 1
fi

# Parameters
VO="$1"
STORAGE="$2"
INFOSYS="ldap://${LCG_GFAL_INFOSYS}"

if [ -z "$VO" ]; then
    echo "Missing VO name" >&2
    echo "$USAGE" >&2
    exit 1
fi

if [ -z "$STORAGE" ]; then
    echo "Missing storage name" >&2
    echo "$USAGE" >&2
    exit 1
fi

# Get VO info
function getPathFromVoInfo {
    query="(&(GlueChunkKey=GlueSEUniqueID=${STORAGE})(|(GlueVOInfoAccessControlBaseRule=VO:${VO})(GlueVOInfoAccessControlBaseRule=${VO}) (GlueVOInfoAccessControlRule=${VO})))"
    ldap_result=`ldapsearch -LLL -x -H "${INFOSYS}" -b "o=grid" "${query}" GlueVOInfoPath | grep GlueVOInfoPath`
    echo `echo ${ldap_result} | cut -d' ' -f 2`
}

# Get VO storage path
function getStoragePath {
    query="(&(GlueSALocalId=${VO})(GlueChunkKey=GlueSEUniqueID=${STORAGE}))"
    ldap_result=`ldapsearch -LLL -x -H "${INFOSYS}" -b "o=grid" "${query}" GlueSAPath | grep GlueSAPath`
    echo `echo ${ldap_result} | cut -d' ' -f 2`
}

home=$(getPathFromVoInfo)
if [ -z "$home" ]; then
    home=$(getStoragePath)
fi
echo $home

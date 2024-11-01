#!/bin/bash

NODES=$1
NTASKS_PER_NODE=${2:-"4"}
TIME_LIMIT=${3:-"01:00:00"}
BIN_=${4:-"./all_reduce_perf"}

# calculate resources from input
CPUS_PER_TASK=$(( 288 / NTASKS_PER_NODE ))
NTASKS=$(( NODES * NTASKS_PER_NODE ))

# set the cpu-bindings
# - 1 task per node: bind to all cores
# - 4 tasks per node: bind tasks to numa nodes
CPUBIND=$([ "$NTASKS_PER_NODE" -eq 1 ] && echo "verbose" || echo "verbose,rank_ldom")

# binary
BIN=$(realpath ${BIN_})
# launch wrapper script
LAUNCHER=$(realpath ./launch_wrapper)
# uenv to run with
UENV=$(realpath ./store_gdr_nccl2.21.5.squashfs)
# jobreport tool
#JOBREPORT=$(realpath ./jobreport)

# output
NODES_STR=$(printf "%04d" "$NODES")
NTASKS_STR=$(printf "%05d" "$NTASKS")
OUTDIR="logs"
POSTFIX="n-${NTASKS_STR}-N-${NODES_STR}"
PREFIX="${OUTDIR}/job-${POSTFIX}"

sbatch <<EOT
#!/bin/bash

#SBATCH --job-name allreduce_bench
#SBATCH --output=${PREFIX}-%j.out
#SBATCH --time=${TIME_LIMIT}
#SBATCH --nodes=${NODES}
#SBATCH --ntasks-per-node=${NTASKS_PER_NODE}
#SBATCH --cpus-per-task=${CPUS_PER_TASK}
#SBATCH --exclusive
#SBATCH --no-requeue
##SBATCH --reservation=daint

set -x

export OMP_NUM_THREADS=${CPUS_PER_TASK}

mkdir -p ${OUTDIR}
REPORT_DIR="${PREFIX}-\${SLURM_JOB_ID}.report"

# uncomment for pytorch/nccl debug logging
#export ENABLE_LOGGING=1

export NCCL_TESTS_DEVICE=0

http_proxy=http://proxy.cscs.ch:8080 https_proxy=https://proxy.cscs.ch:8080 \
srun -u -l \
    --cpu-bind=${CPUBIND} \
    --uenv="${UENV}:/user-environment" \
    ${LAUNCHER} \
    ${BIN} -b 8 -e 4294967296 -f 2 -w 8 -n 24

    #${JOBREPORT} -o \${REPORT_DIR} -- \
#${JOBREPORT} print \${REPORT_DIR}

EOT

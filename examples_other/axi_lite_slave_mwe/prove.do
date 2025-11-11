onerror exit
if {[file exists work]} {
    vdel -lib work -all
}
vlib  work
vmap  work work
vcom  -2008 -work work -autoorder -f work_design.f

## Run PropCheck
formal compile -d olo_axi_lite_slave  -pslfile olo_axi_lite_slave.psl -include_code_cov 
formal coverage enable -code sbceft
formal verify -justify_initial_x -auto_constraint_off -cov_mode

formal generate coverage -detail_all -cov_mode o
formal verify -justify_initial_x -auto_constraint_off -cov_mode reachability
formal generate coverage -detail_all -cov_mode r
formal verify -justify_initial_x -auto_constraint_off -cov_mode signoff
formal generate coverage -detail_all -cov_mode s

exit

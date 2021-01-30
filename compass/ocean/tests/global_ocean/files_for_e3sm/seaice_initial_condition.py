import os
import xarray

from mpas_tools.io import write_netcdf

from compass.io import symlink, add_input_file


def collect(testcase, step):
    """
    Update the dictionary of step properties

    Parameters
    ----------
    testcase : dict
        A dictionary of properties of this test case, which should not be
        modified here

    step : dict
        A dictionary of properties of this step, which can be updated
    """
    defaults = dict(cores=1, min_cores=1, max_memory=1000, max_disk=1000,
                    threads=1)
    for key, value in defaults.items():
        step.setdefault(key, value)

    add_input_file(step, filename='README', target='../README')
    add_input_file(step, filename='restart.nc',
                   target='../{}'.format(step['restart_filename']))

    # for now, we won't define any outputs because they include the mesh short
    # name, which is not known at setup time.  Currently, this is safe because
    # no other steps depend on the outputs of this one.


def run(step, test_suite, config, logger):
    """
    Run this step of the testcase

    Parameters
    ----------
    step : dict
        A dictionary of properties of this step

    test_suite : dict
        A dictionary of properties of the test suite

    config : configparser.ConfigParser
        Configuration options for this test case

    logger : logging.Logger
        A logger for output from the step
    """
    with_ice_shelf_cavities = step['with_ice_shelf_cavities']

    with xarray.open_dataset('restart.nc') as ds:
        mesh_short_name = ds.attrs['MPAS_Mesh_Short_Name']

    try:
        os.makedirs('../assembled_files/inputdata/ocn/mpas-cice/{}'.format(
            mesh_short_name))
    except OSError:
        pass

    restart_filename = os.path.abspath(
        os.path.join('..', step['restart_filename']))
    source_filename = '{}.nc'.format(mesh_short_name)
    dest_filename = 'seaice.{}.nc'.format(mesh_short_name)

    keep_vars = ['areaCell', 'cellsOnCell', 'edgesOnCell', 'fCell',
                 'indexToCellID', 'latCell', 'lonCell', 'meshDensity',
                 'nEdgesOnCell', 'verticesOnCell', 'xCell', 'yCell', 'zCell',
                 'angleEdge', 'cellsOnEdge', 'dcEdge', 'dvEdge', 'edgesOnEdge',
                 'fEdge', 'indexToEdgeID', 'latEdge', 'lonEdge',
                 'nEdgesOnCell', 'nEdgesOnEdge', 'verticesOnEdge',
                 'weightsOnEdge', 'xEdge', 'yEdge', 'zEdge', 'areaTriangle',
                 'cellsOnVertex', 'edgesOnVertex', 'fVertex',
                 'indexToVertexID', 'kiteAreasOnVertex', 'latVertex',
                 'lonVertex', 'xVertex', 'yVertex', 'zVertex']

    if with_ice_shelf_cavities:
        keep_vars.append('landIceMask')

    symlink(restart_filename, source_filename)
    with xarray.open_dataset(source_filename) as ds:
        ds.load()
        ds = ds[keep_vars]
        write_netcdf(ds, dest_filename)

    symlink('../../../../../seaice_initial_condition/{}'.format(dest_filename),
            '../assembled_files/inputdata/ocn/mpas-cice/{}/{}'.format(
                mesh_short_name, dest_filename))

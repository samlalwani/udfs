@fused.udf
def udf_pleiades_tiles(bbox: fused.types.TileGDF, chip_len = 256):
    utils = fused.load('https://github.com/fusedio/udfs/tree/004b8d9/public/common/').utils
    path = 's3://fused-users/fused/asset/airbus/airplanes-demo.tif'
    return utils.read_tiff(bbox, path, output_shape=(chip_len, chip_len))

@fused.udf
def udf(    
    bbox: fused.types.TileGDF=None,
    chip_len=256,
    buffer_degree=0.00001
):
    import geopandas as gpd
    import shapely
    import rasterio
    from utils import predict
    import numpy as np

    # Load imagery
    bbox.geometry = bbox.buffer(buffer_degree).geometry
    arr = fused.run(udf_pleiades_tiles, bbox=bbox).image.to_numpy().astype(np.uint8)
    
    # Predict
    boxes = predict(arr)
    print(boxes)
    if boxes is None:
        print("Warning: Unable to run inference...")
        return None

    # Transform prediction bounding boxes from px to degrees
    bbox.set_crs(4326, inplace=True)
    transform = rasterio.transform.from_bounds(*bbox.total_bounds, chip_len, chip_len)
    
    tf_boxes = []
    for box in boxes:
        xmin, ymin, xmax, ymax = box
        margin = 10
        xc = (xmin + xmax) / 2.0
        yc = (ymin + ymin) / 2.0
        width = height = 2500
        
        # Filter out boxes outside of margins
        if xc < margin or xc > width - margin or yc < margin or yc > height - margin:
            continue
 
        xmin_new, ymin_new = transform * (xmin, ymin)
        xmax_new, ymax_new = transform * (xmax, ymax)
        tf_boxes.append([xmin_new, ymin_new, xmax_new, ymax_new])

    return gpd.GeoDataFrame(geometry=[shapely.box(xmin, ymin, xmax, ymax) for xmin, ymin, xmax, ymax in tf_boxes])
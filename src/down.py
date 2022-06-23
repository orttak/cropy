@staticmethod
def __download_subset_items2(
        item_list,
        aoi,
        band_list, 
        download_path,
        download_status,
        target_epsg,
        cloud_masking,
        scl_list,
        send_s3,
        bucket_name,
        delete_local=True):
        
        result_list=[]
        for item in item_list:
            bands_dict={}
            img_id = item.id
            img_date = str(item.date)
            img_path = os.path.join(download_path,img_date,img_id)
            if not os.path.isdir(download_path):
                os.makedirs(download_path)                        
            if not os.path.isdir(img_path):
                 os.makedirs(img_path)

            if cloud_masking:
                scl_url=item.assets['SCL']['href']
                scl_rds = rioxarray.open_rasterio(scl_url, masked=True, chunks=(1, "auto", -1))
            for band in band_list:
                
                band_url=item.assets[band]['href']
                try:
                    rds = rioxarray.open_rasterio(band_url, masked=True, chunks=(1, "auto", -1))
                except:
                    txt=f'image_id:{item.id},geometry:{item.geometry},date:{item.date} \n'
                    Stac.__create_log_file(target_text=txt,filename=download_path+f'/image_error_{item.id}.txt')
                    continue
                
                #aoi data from http://geojson.io 
                # get aoi as geopandas df
                datajson=json.dumps(aoi)
                target_area=gpd.read_file(datajson)
                #https://geopandas.org/projections.html
                target_area=target_area.to_crs(rds.rio.crs.to_string())

                if cloud_masking:
                    if not rds.rio.resolution()==scl_rds.rio.resolution():
                        scl_rds=scl_rds.rio.reproject(scl_rds.rio.crs,resolution=rds.rio.resolution())
                    
                    scl_clipped =scl_rds.rio.clip(target_area.geometry)
                    classed_img=xr.DataArray(np.in1d(scl_clipped, scl_list).reshape(scl_clipped.shape),
                                            dims=scl_clipped.dims, coords=scl_clipped.coords)
                    clipped =rds.rio.clip(target_area.geometry)
                    clipped=clipped*~classed_img
                    clipped.attrs=rds.attrs
                    rds=None
                else:
                    clipped =rds.rio.clip(target_area.geometry)
                    clipped.attrs=rds.attrs
                    
                if target_epsg:
                    # target_epsg='epsg:4326'
                    clipped = clipped.rio.reproject(target_epsg)
                if download_status:
                    img_name = f'{img_id}_{band}_subset.tif'
                    tif_path = os.path.join(img_path,img_name)
                    clipped.rio.to_raster(tif_path)
                    if send_s3:
                        target_img_path = os.path.join(os.path.basename(download_path),img_date,img_id,img_name)
                        send_file_s3(tif_path,bucket_name,target_img_path)
                        rds=None
                        clipped=None
                        if delete_local:
                            os.remove(tif_path)
                        return 
                band_clipped=clipped.copy()
                bands_dict[band]=band_clipped
                rds=None
            result_list.append(bands_dict)
            
        return result_list
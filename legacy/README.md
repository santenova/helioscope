# Legacy Code


## Tasks

1. **setup:**
    ```
        python3.9 -m venv venv
        source venv/bin/activate
        python3.9 -m pip install -r requirements.txt
        
    ```
2. **creating output dir for image subsets then run:** 
    ```
        mkdir -p clipps
        python3.9 from-image-dir17.py --source data/samples-sdo-aia-1600-week-1-in-2026 --clipps clipps -s 1600 -e 202601
    ```
3. **Post review:**

    ```
    ls clipps
    ```


## Sorry code is a mess (feel free cleanup)



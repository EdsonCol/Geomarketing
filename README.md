# Proyecto de GeoMarketing

Este proyecto realiza análisis de geo-marketing utilizando ArcPy y otras herramientas de análisis espacial. El objetivo principal es calcular áreas de servicio, densidades de empresas y ventas de APH basadas en diferentes capas de datos geográficos.

## Resumen

La aplicación permite:
- Calcular áreas de servicio para estaciones, sitios turísticos y educativos.
- Calcular la densidad de empresas utilizando un análisis de Kernel Density.
- Generar capas filtradas basadas en la intersección de polígonos y puntos.
- Invertir clases de raster y convertir rasters a polígonos.
- Actualizar campos basados en análisis espaciales y cambiar el orden de clases.
- Calcular ventas de APH utilizando múltiples capas de datos.

## Requisitos

Este proyecto requiere ArcPy, que es una biblioteca propietaria que viene incluida con ArcGIS. Asegúrate de tener instalado ArcGIS o ArcGIS Pro para utilizar esta aplicación.

## Instalación

1. **Clona el repositorio**:
    ```bash
    git clone <URL_del_repositorio>
    ```

2. **Navega al directorio del proyecto**:
    ```bash
    cd nombre_del_repositorio
    ```

3. **Configura el entorno de Python de ArcGIS**:

    Asegúrate de activar el entorno de Python que viene con ArcGIS o ArcGIS Pro. Generalmente, este entorno se encuentra en el directorio de instalación de ArcGIS. 

    Por ejemplo, en Windows, podrías hacer lo siguiente (ajusta la ruta según tu instalación de ArcGIS):

    ```bash
    C:\Path\To\ArcGIS\Pro\bin\Python\Scripts\activate.bat
    ```

    O si estás usando Conda:

    ```bash
    conda activate C:\Path\To\ArcGIS\Pro\bin\Python\envs\arcgispro-py3
    ```

4. **Instala las dependencias**:

    Una vez activado el entorno de ArcGIS, instala las dependencias adicionales (como `numpy`) utilizando `pip`:

    ```bash
    pip install numpy
    ```

## Uso

Ejecuta el script principal para realizar los análisis de geo-marketing:

```bash
python main.py

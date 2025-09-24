import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

from gtagora.exception import AgoraException
from gtagora.models.dataset import DatasetType
from gtagora.models.exam import Exam
from gtagora.models.patient import Patient
from gtagora.models.series import Series
from gtagora.models.vendor import Vendor


@dataclass
class ImportDataset:
    type: str
    files: List[str]

    def to_json(self):
        return {
            "Type": self.type,
            "Files": [{"File": Path(f).name, "ParameterSetID": None} for f in self.files],
            "ParameterSetID": None
        }


def create_datasets(files: List[Path]) -> List[ImportDataset]:
    """
    Groups files by their extensions based on predefined extension groups with types.

    Args:
        files: List of file paths as pathlib Path objects

    Returns:
        List of ImportDataset objects, where each contains a type and files that belong together
    """
    # Define which file extensions belong together with their types
    extension_groups = [
        {'type': 'RAW_LAB', 'extensions': {'.lab', '.raw'}},
        {'type': 'REC_PAR', 'extensions': {'.par', '.rec'}},
        {'type': 'PHILIPS_SPECTRO', 'extensions': {'.sdat', '.spar'}},
        {'type': 'SINFILE', 'extensions': {'.sin'}},
        {'type': 'DICOM_IMAGE', 'extensions': {'.dcm'}},
        {'type': 'TWIX', 'extensions': {'.dat'}},
        {'type': 'SIEMENS_PRO', 'extensions': {'.pro'}},
        {'type': 'ISMRMRD', 'extensions': {'.h5'}},
        {'type': 'NIFTI1', 'extensions': {'.nii'}},
        # Add more extension groups as needed
    ]

    # Create a mapping from extension to group info
    ext_to_group = {}
    for group in extension_groups:
        for ext in group['extensions']:
            ext_to_group[ext] = {
                'type': group['type'],
                'group_id': id(group)  # Use object id to distinguish groups with same type
            }

    # Group files by their group ID or create individual groups for unmatched extensions
    groups = {}
    individual_files: List[str] = []

    for file_path in files:
        # Extract the file extension (convert to lowercase for case-insensitive matching)
        ext = file_path.suffix.lower()

        if ext in ext_to_group:
            # File belongs to a predefined group
            group_info = ext_to_group[ext]
            group_id = group_info['group_id']
            if group_id not in groups:
                groups[group_id] = {
                    'type': group_info['type'],
                    'files': []
                }
            groups[group_id]['files'].append(file_path)
        else:
            # File doesn't belong to any predefined group, create individual group
            individual_files.append(file_path.name)

    # Convert groups to list of ImportDataset objects
    result = []

    # Add grouped files (group by basename within the same extension group)
    for group_info in groups.values():
        # Group files by basename within the same extension group
        basename_groups = {}
        for file_path in group_info['files']:
            basename = file_path.stem  # Gets the filename without extension
            if basename not in basename_groups:
                basename_groups[basename] = []
            basename_groups[basename].append(file_path.name)

        # Add each basename group as an ImportDataset
        for basename_files in basename_groups.values():
            result.append(ImportDataset(
                type=group_info['type'],
                files=sorted(basename_files)
            ))

    # Add individual files as single-item ImportDataset with 'unknown' type
    for file_path in individual_files:
        result.append(ImportDataset(
            type='OTHER',
            files=[str(file_path)]
        ))

    return result


def create_import_json(vendor: str = None, type: str = None, exam: Exam = None, series: Series = None, patient: Patient = None, files: List[Path] = None) -> dict:
    types = [
        "REL3",
        "REL5",
        "DICOM",
        "Bruker",
        "RAW_VB",
        "RAW_VC",
        "RAW_VD",
        "RAW_VE",
        "ISMRMRD",
        "PATCH",
        "PRO",
        "ExamCard",
        ""
      ]

    if not vendor and exam and hasattr(exam, 'vendor'):
        if isinstance(exam.vendor, int):
            vendors = Vendor.get_list(http_client=exam.http_client)
            vendor = next((v.name for v in vendors if v.id == exam.vendor), "Unknown")
        else:
            vendorObj = Vendor.from_response(exam.vendor, http_client=exam.http_client)
            vendor = vendorObj.name if vendorObj and hasattr(vendorObj, 'name') else "Unknown"

    vendor = vendor if vendor else "Unknown"
    vendors = [
        "Unknown",
        "Philips",
        "Bruker",
        "Siemens",
        "GE"
      ]
    if vendor not in vendors:
        raise AgoraException(f'The vendor {vendor} is not supported. Supported vendors are: {vendors}')

    if vendor == "Philips" and not type:
        type = "REL5"
    if vendor == "Siemens" and not type:
        type = "RAW_VD"
    if vendor == "Bruker" and not type:
        type = "Bruker"
    if vendor == "GE" and not type:
        type = "ISMRMRD"

    type = type if type else ""

    datasets = create_datasets(files) if files else []
    # check if there is a DICOM dataset
    has_dicom = any(d.type == 'DICOM' for d in datasets)
    if has_dicom:
        type = "DICOM"

    if type not in types:
        raise AgoraException(f'The type {type} is not supported. Supported types are: {types}')

    if not patient and exam and hasattr(exam, 'patient'):
        if isinstance(exam.patient, dict):
            patient = Patient.from_response(exam.patient, http_client=exam.http_client)
        elif isinstance(exam.patient, int):
            patient = Patient.get(exam.patient, http_client=exam.http_client)

    exam_start_date = getattr(exam, "start_time", None) if exam else None
    exam_start_date = datetime.fromisoformat(exam_start_date) if exam_start_date else None
    exam_date = exam_start_date.strftime("%d.%m.%Y") if exam_start_date else "01.01.1900"
    exam_time = exam_start_date.strftime("%H:%M:%S") if exam_start_date else "00:00:00"

    birthdate = getattr(patient, "birth_date", None) if patient else None
    birthdate = datetime.fromisoformat(birthdate) if birthdate else None
    birthdate = birthdate.strftime("%d.%m.%Y") if birthdate else "01.01.1900"

    series_time = getattr(series, "time", None) if exam else None
    series_time = datetime.fromisoformat(series_time) if series_time else None
    series_date = series_time.strftime("%d.%m.%Y") if series_time else exam_date
    series_time = series_time.strftime("%H:%M:%S.%f") if series_time else exam_time

    datasets_dict = [d.to_json() for d in datasets] if datasets else []
    json = {
        "Creator": "gtagora-connector-py",
        "Version": "2.0.0",
        "Vendor": vendor,
        "Type": type,
        "Datasets": datasets_dict,
        "ImportParameter": {
            "Exam": {
                "Date": exam_date,
                "Description": getattr(exam, "description", "") if exam else "",
                "DeviceName": getattr(exam, "scanner_name", "") if exam else "",
                "Name": getattr(exam, "name", "") if exam else "",
                "Time": exam_time,
                "UID": getattr(exam, "uid", str(uuid.uuid4())) if exam else str(uuid.uuid4())
            },
            "Patient": {
                "BirthDate": birthdate,
                "Gender": getattr(patient, "sex", "O").upper() if patient else "O",
                "Name": getattr(patient, "name", "") if patient else "",
                "UID": getattr(patient, "patient_id", str(uuid.uuid4())) if patient else str(uuid.uuid4()),
                "Weight": getattr(patient, "weight", 70) if patient else 70
            },
            "Series": {
                "AcquisitionNumber": getattr(series, "acquisition_number", 0) if series else 0,
                "Date": series_date,
                "Name": getattr(series, "name", "New Series") if series else "New Series",
                "ReferenceScanUIDs": [],
                "Time": series_time,
                "TypeLabel": "",
                "UID": getattr(series, "uid", str(uuid.uuid4())) if series else str(uuid.uuid4())
            }
        },
        "ParameterSets": []
    }

    return json
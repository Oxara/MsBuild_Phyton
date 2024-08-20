import datetime
import enum
import subprocess
import shutil
import os
import asyncio

class BuildConfigEnum(enum.Enum):
    Debug = "Debug"
    Release = "Release"

class BuildTypeEnum(enum.Enum):
    Build = "Build"
    Publish = "Publish"

class BuildResultEnum(enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED" 

class BuildManager:
    def __init__(self, project_root, target_folder, nuget_target_folder, net_version, config_mode, type_mode):
        self.project_root = project_root
        self.target_folder = target_folder
        self.nuget_target_folder = nuget_target_folder
        self.net_version = net_version
        self.config_mode = config_mode
        self.type_mode = type_mode
        self.line_length = 100  # DrawLine method için karakter uzunluğu

    def project_folder(self, folder_name):
        return os.path.join(self.project_root, folder_name)

    def build_result_folder(self, folder_name):
        if self.type_mode == BuildTypeEnum.Publish:
            return os.path.join(self.project_folder(folder_name), r"bin", self.config_mode.name, self.net_version, self.type_mode.name.lower())
        else:
            return os.path.join(self.project_folder(folder_name), r"bin", self.config_mode.name, self.net_version)

    def build_nuget_folder(self, folder_name):
        return os.path.join(self.project_folder(folder_name), r"bin", self.config_mode.name)

    def draw_line(self, char):
        print(char * self.line_length)

    async def build(self, project_folder, build_results):
        project_folder = self.project_folder(project_folder)
        build_folder = self.build_result_folder(project_folder)
        nuget_folder = self.build_nuget_folder(project_folder)

        self.draw_line('-')
        print("  Processed At   : " + str(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
        print("  Build Config   : " + self.config_mode.name)
        print("  Build Type     : " + self.type_mode.name)
        print("  NET Version    : " + self.net_version)
        print("  Project Folder : " + project_folder)
        print("  Build Folder   : " + build_folder)
        print("  Target Folder  : " + self.target_folder)
        print("  Nuget Folder   : " + self.nuget_target_folder)
        self.draw_line('-')

        os.chdir(project_folder)

        command_args = ['dotnet', self.type_mode.name.lower(), '-c', self.config_mode.name]
        publish_process = await asyncio.create_subprocess_exec(
            *command_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await publish_process.communicate()

        if publish_process.returncode != 0:
            self.draw_line('-')
            print(stdout.decode())
            print(stderr.decode())
            self.draw_line('-')
            build_results.append((project_folder, BuildResultEnum.FAILED, stdout.decode()))
        else:
            self.copy_dll_files(build_folder)
            self.copy_pdb_files(build_folder)
            self.copy_nupkg_files(nuget_folder)
            build_results.append((project_folder, BuildResultEnum.SUCCESS, stdout.decode()))

    def copy_dll_files(self, build_folder):
        # if self.config_mode == BuildConfigEnum.Debug:
        print("COPYING Dll Files...")   
        file_list = [file for file in os.listdir(build_folder) if file.startswith('Framework') and file.endswith('.dll')]
        for file in file_list:
            if any(name in file for name in DoNotCopy):
                continue
            shutil.copy(os.path.join(build_folder, file), self.target_folder)
            print("COPIED: " + file) 
        self.draw_line('-')

    def copy_pdb_files(self, build_folder):
        if self.config_mode == BuildConfigEnum.Debug:
            print("COPYING Pdb Files...")   
            file_list = [file for file in os.listdir(build_folder) if file.startswith('Framework') and file.endswith('.pdb')]
            for file in file_list:
                if any(name in file for name in DoNotCopy):
                    continue
                shutil.copy(os.path.join(build_folder, file), self.nuget_target_folder)
                print("COPIED: " + file)         
            self.draw_line('-')

    def copy_nupkg_files(self, nuget_folder):
        if self.config_mode == "asdas":
            print("COPYING Nupkg Files...")   
            file_list = [file for file in os.listdir(nuget_folder) if file.startswith('Framework') and file.endswith('.nupkg')]
            for file in file_list:
                if any(name in file for name in DoNotCopy):
                    continue
                shutil.copy(os.path.join(nuget_folder, file), self.nuget_target_folder)
                print("COPIED: " + file)         
            self.draw_line('-')           

    async def build_and_extract_files(self):
        build_results = []

        # No Dependency
        await self.build(r"Core\Framework.Core.Extension", build_results)
        await self.build(r"Core\Framework.Core.Serializer", build_results)
        await self.build(r"Global\Framework.Global.Model", build_results)
        await self.build(r"Core\Framework.Core.Xslt", build_results)

        # Core With Dependency
        await self.build(r"Core\Framework.Core.Encryption", build_results)
        await self.build(r"Core\Framework.Core.HandleBar", build_results)
        await self.build(r"Core\Framework.Core.IO", build_results)
        await self.build(r"Core\Framework.Core.LDAP", build_results)
        await self.build(r"Core\Framework.Core.Mapping", build_results)
        await self.build(r"Core\Framework.Core.Pdf", build_results)
        await self.build(r"Core\Framework.Core.Smtp", build_results)
        await self.build(r"Core\Framework.Core.SpreadSheet", build_results)
        await self.build(r"Core\Framework.Core.Zip", build_results)

        # Infrastructure With Dependency
        await self.build(r"Infrastructure\Framework.Infrastructure.Swagger", build_results)
        await self.build(r"Infrastructure\Framework.Infrastructure.RabbitMQ", build_results)
        await self.build(r"Infrastructure\Framework.Infrastructure.ElasticSearch", build_results)
        await self.build(r"Infrastructure\Framework.Infrastructure.Cache", build_results)

        # EF With Dependency
        await self.build(r"EntityFramework\Framework.EntityFramework.DB", build_results)
        await self.build(r"EntityFramework\Framework.EntityFramework.Repository", build_results)

        # Application With Dependency
        await self.build(r"Application\Framework.Application.Definitions", build_results)
        await self.build(r"Application\Framework.Application.Model", build_results)
        await self.build(r"Application\Framework.Application.Repository", build_results)
        await self.build(r"Application\Framework.Application.Validation", build_results)
        await self.build(r"Application\Framework.Application.Services", build_results)

        # API With Dependency
        # await self.build(r"Presantation\Framework.Presantation.WebAPI", build_results)

        # Print summary
        self.draw_line('-')
        print("SUMMARY OF BUILD RESULTS")
        self.draw_line('-')
        for result in build_results:
            project_folder, status, message = result
            if status ==  BuildResultEnum.SUCCESS:
                print(f"Project Folder: {project_folder} => {status.value}") 
            else:
                print(f"Project Folder: {project_folder} => {status.value}, Output: {message}") 
        self.draw_line('-')

# Değişkenler
DoNotCopy = ["Framework.Presantation.WebAPI", "Framework.Global.IOC", "Framework.Application.Job"]
ProjectRoot = r"C:\PROJECT\code.vbt.com.tr\Framework\Draft.Framework"
TargetFolder = r"C:\PROJECT\code.vbt.com.tr\HR\EnterpriseHR\enterprisehr.api\Package\Framework.Package\ExternalDll"
NugetTargetFolder = r"C:\Users\erdem.ozkara\Desktop\NugetFolder"
NetVersion = "net8.0"

ConfigMode = BuildConfigEnum.Release
TypeMode = BuildTypeEnum.Publish

# Asenkron fonksiyonu çalıştırma
asyncio.run(BuildManager(ProjectRoot, TargetFolder, NugetTargetFolder, NetVersion, ConfigMode, TypeMode).build_and_extract_files())

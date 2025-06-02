SERVICE_PATH_CUES = [
    {
        "ServiceName": "hubServer",
        "SearchCues": [
            {"sub_dir": "hub", "filename_pattern": "Start.bat"},
            {"sub_dir": "hub", "filename_pattern": "hub.exe"},
            {"filename_pattern": "hubServer.bat"},
            {"filename_pattern": "hubServer.exe"}
        ]
    },
    {
        "ServiceName": "hubGateway",
        "SearchCues": [
            {"sub_dir": "hubGateway", "filename_pattern": "Start.bat"},
            {"sub_dir": "hubGateway", "filename_pattern": "hubGateway.bat"},
            {"sub_dir": "hubGateway", "filename_pattern": "hubGateway.exe"},
            {"sub_dir": "hub", "filename_pattern": "hubGateway.exe"}, # Common hub directory
            {"sub_dir": "hub", "filename_pattern": "hubGateway.bat"},
            {"filename_pattern": "hubGateway.bat"},
            {"filename_pattern": "hubGateway.exe"}
        ]
    },
    {
        "ServiceName": "SteerHub",
        "SearchCues": [
            {"sub_dir": "SteerHub", "filename_pattern": "Start.bat"},
            {"sub_dir": "SteerHub", "filename_pattern": "SteerHub.bat"},
            {"sub_dir": "SteerHub", "filename_pattern": "SteerHub.exe"},
            {"filename_pattern": "SteerHub.bat"},
            {"filename_pattern": "SteerHub.exe"}
        ]
    },
    {
        "ServiceName": "SteerSession",
        "SearchCues": [
            {"sub_dir": "SteerSession", "filename_pattern": "Start.bat"},
            {"sub_dir": "SteerSession", "filename_pattern": "SteerSession.bat"},
            {"sub_dir": "SteerSession", "filename_pattern": "SteerSession.exe"},
            {"filename_pattern": "SteerSession.bat"},
            {"filename_pattern": "SteerSession.exe"}
        ]
    },
    {
        "ServiceName": "SteerMind",
        "SearchCues": [
            {"sub_dir": "SteerMind", "filename_pattern": "Start.bat"},
            {"sub_dir": "SteerMind", "filename_pattern": "SteerMind.bat"},
            {"sub_dir": "SteerMind", "filename_pattern": "SteerMind.exe"},
            {"filename_pattern": "SteerMind.bat"},
            {"filename_pattern": "SteerMind.exe"}
        ]
    },
    {
        "ServiceName": "SteerCast",
        "SearchCues": [
            {"sub_dir": "SteerCast", "filename_pattern": "Start.bat"},
            {"sub_dir": "SteerCast", "filename_pattern": "SteerCast.bat"},
            {"sub_dir": "SteerCast", "filename_pattern": "SteerCast.exe"},
            {"filename_pattern": "SteerCast.bat"},
            {"filename_pattern": "SteerCast.exe"}
        ]
    },
    {
        "ServiceName": "SteerGateway",
        "SearchCues": [
            {"sub_dir": "SteerGateway", "filename_pattern": "Start.bat"},
            {"sub_dir": "SteerGateway", "filename_pattern": "SteerGateway.bat"},
            {"sub_dir": "SteerGateway", "filename_pattern": "SteerGateway.exe"},
            {"filename_pattern": "SteerGateway.bat"},
            {"filename_pattern": "SteerGateway.exe"}
        ]
    },
    {
        "ServiceName": "SteerWeb",
        "SearchCues": [
            {"sub_dir": "SteerWeb", "filename_pattern": "Start.bat"},
            {"sub_dir": "SteerWeb", "filename_pattern": "SteerWeb.bat"},
            {"sub_dir": "SteerWeb", "filename_pattern": "SteerWeb.exe"},
            {"filename_pattern": "SteerWeb.bat"},
            {"filename_pattern": "SteerWeb.exe"}
        ]
    },
    {
        "ServiceName": "BoxApi",
        "SearchCues": [
            {"sub_dir": "BoxApi", "filename_pattern": "Start.bat"},
            {"sub_dir": "BoxApi", "filename_pattern": "BoxApi.bat"},
            {"sub_dir": "BoxApi", "filename_pattern": "BoxApi.exe"},
            {"filename_pattern": "BoxApi.bat"},
            {"filename_pattern": "BoxApi.exe"}
        ]
    },
    {
        "ServiceName": "BoxWeb",
        "SearchCues": [
            {"sub_dir": "BoxWeb", "filename_pattern": "Start.bat"},
            {"sub_dir": "BoxWeb", "filename_pattern": "BoxWeb.bat"},
            {"sub_dir": "BoxWeb", "filename_pattern": "BoxWeb.exe"},
            {"filename_pattern": "BoxWeb.bat"},
            {"filename_pattern": "BoxWeb.exe"}
        ]
    },
    {
        "ServiceName": "TeraApi",
        "SearchCues": [
            {"sub_dir": "TeraApi", "filename_pattern": "Start.bat"},
            {"sub_dir": "TeraApi", "filename_pattern": "TeraApi.bat"},
            {"sub_dir": "TeraApi", "filename_pattern": "TeraApi.exe"},
            {"filename_pattern": "TeraApi.bat"},
            {"filename_pattern": "TeraApi.exe"}
        ]
    },
    {
        "ServiceName": "NexusServer",
        "SearchCues": [
            {"sub_dir": "NexusServer", "filename_pattern": "Start.bat"},
            {"sub_dir": "NexusServer", "filename_pattern": "NexusServer.bat"},
            {"sub_dir": "NexusServer", "filename_pattern": "NexusServer.exe"},
            {"sub_dir": "Executable/Bin", "filename_pattern": "*. NexusServer.bat"},
            {"sub_dir": "Executable/Bin", "filename_pattern": "NexusServer.bat"},
            {"filename_pattern": "NexusServer.bat"},
            {"filename_pattern": "NexusServer.exe"}
        ]
    },
    {
        "ServiceName": "LogServer",
        "SearchCues": [
            {"sub_dir": "LogServer", "filename_pattern": "Start.bat"},
            {"sub_dir": "LogServer", "filename_pattern": "LogServer.bat"},
            {"sub_dir": "LogServer", "filename_pattern": "LogServer.exe"},
            {"filename_pattern": "LogServer.bat"},
            {"filename_pattern": "LogServer.exe"}
        ]
    },
    {
        "ServiceName": "TopographyServer",
        "SearchCues": [
            {"sub_dir": "TopographyServer", "filename_pattern": "Start.bat"},
            {"sub_dir": "TopographyServer", "filename_pattern": "TopographyServer.bat"},
            {"sub_dir": "TopographyServer", "filename_pattern": "TopographyServer.exe"},
            {"filename_pattern": "TopographyServer.bat"},
            {"filename_pattern": "TopographyServer.exe"}
        ]
    },
    {
        "ServiceName": "ArbiterServer",
        "SearchCues": [
            {"sub_dir": "Executable/Bin", "filename_pattern": "*. ArbiterServer.bat"},
            {"sub_dir": "Executable/Bin", "filename_pattern": "ArbiterServer.bat"},
            {"sub_dir": "ArbiterServer", "filename_pattern": "Start.bat"},
            {"sub_dir": "arbiter", "filename_pattern": "Start.bat"},
            {"filename_pattern": "ArbiterServer.bat"},
            {"filename_pattern": "ArbiterServer.exe"}
        ]
    },
    {
        "ServiceName": "ArbiterGateway",
        "SearchCues": [
            {"sub_dir": "ArbiterGateway", "filename_pattern": "Start.bat"},
            {"sub_dir": "ArbiterGateway", "filename_pattern": "ArbiterGateway.bat"},
            {"sub_dir": "ArbiterGateway", "filename_pattern": "ArbiterGateway.exe"},
            {"sub_dir": "Executable/Bin", "filename_pattern": "*. ArbiterGateway.bat"},
            {"sub_dir": "Executable/Bin", "filename_pattern": "ArbiterGateway.bat"},
            {"filename_pattern": "ArbiterGateway.bat"},
            {"filename_pattern": "ArbiterGateway.exe"}
        ]
    },
    {
        "ServiceName": "WorldServer",
        "SearchCues": [
            {"sub_dir": "Executable/Bin", "filename_pattern": "*. WorldServer.bat"},
            {"sub_dir": "Executable/Bin", "filename_pattern": "WorldServer.bat"},
            {"sub_dir": "WorldServer", "filename_pattern": "Start.bat"},
            {"sub_dir": "world", "filename_pattern": "Start.bat"},
            {"filename_pattern": "WorldServer.bat"},
            {"filename_pattern": "WorldServer.exe"}
        ]
    },
    {
        "ServiceName": "DungeonServer",
        "SearchCues": [
            {"sub_dir": "DungeonServer", "filename_pattern": "Start.bat"},
            {"sub_dir": "DungeonServer", "filename_pattern": "DungeonServer.bat"},
            {"sub_dir": "DungeonServer", "filename_pattern": "DungeonServer.exe"},
            {"sub_dir": "Executable/Bin", "filename_pattern": "*. DungeonServer.bat"},
            {"sub_dir": "Executable/Bin", "filename_pattern": "DungeonServer.bat"},
            {"filename_pattern": "DungeonServer.bat"},
            {"filename_pattern": "DungeonServer.exe"}
        ]
    },
    {
        "ServiceName": "PartyMatching",
        "SearchCues": [
            {"sub_dir": "PartyMatching", "filename_pattern": "Start.bat"},
            {"sub_dir": "PartyMatching", "filename_pattern": "PartyMatching.bat"},
            {"sub_dir": "PartyMatching", "filename_pattern": "PartyMatching.exe"},
            {"filename_pattern": "PartyMatching.bat"},
            {"filename_pattern": "PartyMatching.exe"}
        ]
    },
    {
        "ServiceName": "BattleFieldsServer",
        "SearchCues": [
            {"sub_dir": "BattleFieldsServer", "filename_pattern": "Start.bat"},
            {"sub_dir": "BattleFieldsServer", "filename_pattern": "BattleFieldsServer.bat"},
            {"sub_dir": "BattleFieldsServer", "filename_pattern": "BattleFieldsServer.exe"},
            {"filename_pattern": "BattleFieldsServer.bat"},
            {"filename_pattern": "BattleFieldsServer.exe"}
        ]
    },
    {
        "ServiceName": "Steer", # General 'Steer' app
        "SearchCues": [
            {"sub_dir": "Steer", "filename_pattern": "Start.bat"},
            {"sub_dir": "Steer", "filename_pattern": "Steer.bat"},
            {"sub_dir": "Steer", "filename_pattern": "Steer.exe"},
            {"filename_pattern": "Steer.bat"},
            {"filename_pattern": "Steer.exe"}
        ]
    }
]

if __name__ == '__main__':
    import json
    # Verify the structure and count
    print(f"Generated {len(SERVICE_PATH_CUES)} service cue entries.")
    # Print one entry as an example
    if SERVICE_PATH_CUES:
        print("\nExample entry (hubServer):")
        print(json.dumps(SERVICE_PATH_CUES[0], indent=4))

    arbiter_server_entry = next((item for item in SERVICE_PATH_CUES if item["ServiceName"] == "ArbiterServer"), None)
    if arbiter_server_entry:
        print("\nExample entry (ArbiterServer):")
        print(json.dumps(arbiter_server_entry, indent=4))

    world_server_entry = next((item for item in SERVICE_PATH_CUES if item["ServiceName"] == "WorldServer"), None)
    if world_server_entry:
        print("\nExample entry (WorldServer):")
        print(json.dumps(world_server_entry, indent=4))

    # Verify a generic one
    steer_mind_entry = next((item for item in SERVICE_PATH_CUES if item["ServiceName"] == "SteerMind"), None)
    if steer_mind_entry:
        print("\nExample entry (SteerMind - generic fallback):")
        print(json.dumps(steer_mind_entry, indent=4))

```

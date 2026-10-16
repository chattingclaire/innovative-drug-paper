"""Persist only constructed fixtures and a no-transport run. Never codes real policy."""
import json
from adapter import ROOT
from toy_tests import fixture, PNG, MANUAL, response_fixture
from runner import offline_prepare, execute, exclusive_json

def main():
    toy = ROOT / 'toy'
    toy.mkdir(exist_ok=False)
    packet, assets = fixture()
    (toy / 'toy.png').write_bytes(PNG)
    exclusive_json(toy / 'source.constructed.json', packet)
    exclusive_json(toy / 'assets.constructed.json', assets)
    exclusive_json(toy / 'response.constructed.json', response_fixture(packet, null=True))
    prepared = offline_prepare(packet, assets, toy, MANUAL, toy_amendment=True)
    state = execute(prepared, toy / 'offline-not-executed')
    exclusive_json(toy / 'README-status.json', {
        'scope': 'constructed_toy_only', 'image': 'one-pixel constructed asset, not a policy source scan',
        'response': 'hand-constructed contract fixture, not a model response or gold label',
        'offline_state': state['state'], 'actual_model_calls': 0, 'real_policy_units_coded': 0})
    print(json.dumps({'state': state['state'], 'actual_model_calls': 0, 'real_policy_units_coded': 0}, ensure_ascii=False))

if __name__ == '__main__':
    main()

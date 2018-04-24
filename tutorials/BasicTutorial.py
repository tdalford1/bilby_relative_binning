import numpy as np
import pylab as plt

import dynesty.plotting as dyplot
import corner
import peyote

peyote.utils.setup_logger()

time_duration = 1.
sampling_frequency = 4096.

injection_parameters = dict(
    mass_1=36.,
    mass_2=29.,
    spin11=0,
    spin12=0,
    spin13=0,
    spin21=0,
    spin22=0,
    spin23=0,
    luminosity_distance=100.,
    iota=0.4,
    phase=1.3,
    waveform_approximant='IMRPhenomPv2',
    reference_frequency=50.,
    ra=1.375,
    dec=-1.2108,
    geocent_time=1126259642.413,
    psi=2.659
)
simulation_parameters = injection_parameters.copy()
simulation_parameters = peyote.parameter.Parameter.parse_floats_to_parameters(simulation_parameters)
# Create the waveform_generator using a LAL BinaryBlackHole source function
waveform_generator = peyote.waveform_generator.WaveformGenerator(
    sampling_frequency=sampling_frequency,
    time_duration=time_duration,
    source_model=peyote.source.lal_binary_black_hole,
    parameters=simulation_parameters)
hf_signal = waveform_generator.frequency_domain_strain()

# sampling_parameters = peyote.parameter.Parameter.\
#    parse_floats_to_parameters(simulation_parameters)

# sampling_parameters = peyote.parameter.Parameter.\
#    parse_keys_to_parameters(simulation_parameters.keys())


# Simulate the data in H1
H1 = peyote.detector.H1
H1.set_data(sampling_frequency=sampling_frequency, duration=time_duration,
            from_power_spectral_density=True)
H1.inject_signal(waveform_polarizations=hf_signal, parameters=simulation_parameters)

# Simulate the data in L1
L1 = peyote.detector.L1
L1.set_data(sampling_frequency=sampling_frequency, duration=time_duration,
            from_power_spectral_density=True)
L1.inject_signal(waveform_polarizations=hf_signal, parameters=simulation_parameters)

# Simulate the data in V1
V1 = peyote.detector.V1
V1.set_data(sampling_frequency=sampling_frequency, duration=time_duration,
            from_power_spectral_density=True)
V1.inject_signal(waveform_polarizations=hf_signal, parameters=simulation_parameters)

IFOs = [H1, L1, V1]

# Plot the noise and signal
fig, ax = plt.subplots()
plt.loglog(H1.frequency_array, np.abs(H1.data), lw=1.5, label='H1 noise+signal')
plt.loglog(H1.frequency_array, H1.amplitude_spectral_density_array, lw=1.5, label='H1 ASD')
plt.loglog(L1.frequency_array, np.abs(L1.data), lw=1.5, label='L1 noise+signal')
plt.loglog(L1.frequency_array, L1.amplitude_spectral_density_array, lw=1.5, label='H1 ASD')
# plt.loglog(frequencies, np.abs(hf_signal['plus']), lw=0.8, label='signal')
plt.xlim(10, 1000)
plt.legend()
plt.xlabel(r'frequency')
plt.ylabel(r'strain')
fig.savefig('data')

likelihood = peyote.likelihood.Likelihood(IFOs, waveform_generator)

# New way way of doing it, still not perfect
# simulation_parameters['mass_1'].prior = peyote.prior.Uniform(lower=35, upper=37)
# simulation_parameters['luminosity_distance'].prior = peyote.prior.Uniform(lower=30, upper=200)
simulation_parameters["geocent_time"].prior = peyote.prior.Uniform(lower=injection_parameters["geocent_time"]-0.1,
                                                                   upper=injection_parameters["geocent_time"]+0.1)

result = peyote.sampler.run_sampler(likelihood, priors=sampling_parameters, sampler='nestle', verbose=True)
print(result)
truths = [simulation_parameters[x] for x in result.search_parameter_keys]


fig = corner.corner(result.samples, truths=truths, labels=result.search_parameter_keys)
fig.savefig('corner')

fig, axes = dyplot.traceplot(result['sampler_output'])
fig.savefig('trace')

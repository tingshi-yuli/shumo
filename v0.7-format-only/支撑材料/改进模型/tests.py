"""Numerical contract tests for the proposed solver."""
import unittest
import importlib.util
import numpy as np

class TestFlux(unittest.TestCase):
    def test_integrated_diffusivity(self):
        self.assertIsNotNone(importlib.util.find_spec('model'), 'integral-flux solver is not implemented yet')
        from model import integral_diffusivity
        actual=integral_diffusivity(3,np.array([.05]),np.array([.15]),np.array([50.165]),order=16)
        self.assertAlmostEqual(float(actual[0])/2.580097788700743e-10,1.,places=10)

    def test_equal_concentrations(self):
        self.assertIsNotNone(importlib.util.find_spec('model'), 'integral-flux solver is not implemented yet')
        from model import integral_diffusivity, properties
        c=np.array([.05,.15,1.,2.55]);t=np.array([28.,35.,50.,50.165])
        ref=properties(3,c,t)[2]
        np.testing.assert_allclose(integral_diffusivity(3,c,c,t),ref,rtol=1e-13)

    def test_no_flux_conservation_and_equilibrium(self):
        from model import Solver,Config
        s=Solver(Config(n=40));u=1+s.x**2
        new=s.linear_step(u,np.full(40,1e-8),np.ones(41),0.,0.,.02,30.)
        self.assertLess(abs(float(s.volume@(new-u))),1e-13)
        same=s.linear_step(np.full(41,.7),np.full(40,1e-8),np.ones(41),8e-7,.7,.02,30.)
        np.testing.assert_allclose(same,.7,rtol=1e-13)

    def test_cylindrical_bessel_decay(self):
        from scipy.special import j0,j1
        from model import Solver,Config
        s=Solver(Config(n=80));D=1e-7;R=.02;z=1.
        h=D*z*j1(z)/(R*j0(z));u=j0(z*s.x)
        for _ in range(1000):u=s.linear_step(u,np.full(80,D),np.ones(81),h,0.,R,.1)
        exact=j0(z*s.x)*np.exp(-D*z*z*100/R**2)
        self.assertLess(float(np.max(abs(u-exact))),1e-5)

    def test_integral_flux_symmetry_and_positivity(self):
        from model import integral_diffusivity
        a=np.array([.05,.15,1.]);b=np.array([.2,2.55,.06]);t=np.array([28.,50.,40.])
        f=integral_diffusivity(3,a,b,t,16)
        np.testing.assert_allclose(f,integral_diffusivity(3,b,a,t,16),rtol=1e-13)
        self.assertTrue(np.all(f>0))

    def test_wet_fraction_crossing(self):
        from model import Solver,Config
        s=Solver(Config(n=20));c=.2-.1*s.x
        snap=s.snapshot(0,np.full(21,28.),c)
        self.assertAlmostEqual(snap['wet_fraction'],.25,places=12)

    def test_wet_fraction_multiple_regions_and_threshold_equality(self):
        from model import Solver,Config
        s=Solver(Config(n=4,grid_power=1))
        snap=s.snapshot(0,np.full(5,28.),np.array([.2,.1,.2,.1,.2]))
        # Wet intervals: [0,1/8], [3/8,5/8], [7/8,1].
        self.assertAlmostEqual(snap['wet_fraction'],.5,places=12)
        equal=s.snapshot(0,np.full(5,28.),np.full(5,.15))
        self.assertEqual(equal['wet_fraction'],1.)

    def test_zero_shrinkage_reduces_to_fixed_radius(self):
        from model import Solver,Config
        class ConstantRadiusInputs:
            def boundary(self,t,environment='last'): return 50.,.05
            def radius(self,t,shrink): return .02
        args=dict(material=4,n=10,max_time=60,stop_dry=False)
        a=Solver(Config(**args,shrink=False),ConstantRadiusInputs()).run()
        b=Solver(Config(**args,shrink=True),ConstantRadiusInputs()).run()
        np.testing.assert_array_equal(a['final']['T'],b['final']['T'])
        np.testing.assert_array_equal(a['final']['C'],b['final']['C'])

    def test_moving_sample_uses_physical_radius_and_outside_blanks(self):
        from model import sample
        snapshot={'radius_cm':1.2,'C':[.6,.4,.2]}
        actual=sample(snapshot,'C',[0.,.5,1.,1.2,1.3,2.])
        np.testing.assert_allclose(actual[:4],[.6,13/30,4/15,.2],atol=1e-14)
        self.assertEqual(actual[4:],[None,None])

    def test_radius_data_do_not_silently_extrapolate(self):
        from model import Inputs
        inputs=Inputs()
        with self.assertRaisesRegex(ValueError,'extrapolation'):
            inputs.radius(float(inputs.radii[-1,0])+1,True)


    def test_full_output_lands_on_every_second(self):
        from model import Solver,Config
        result=Solver(Config(n=10,early_dt=10,keep_short=True,
                             output_stride=1,max_time=60,stop_dry=False)).run()
        self.assertEqual([s['t'] for s in result['short']],list(range(61)))

    def test_boundary_study_nominal_preserves_kernel(self):
        from model import Solver,Config
        from p2_study import BoundaryStudy
        for moving in (False,True):
            cfg=Config(material=4 if moving else 3,shrink=moving,n=160,
                       max_time=120,stop_dry=False,output_stride=1)
            a=Solver(cfg).run(); b=BoundaryStudy(cfg).run()
            for field in ('T','C'):
                np.testing.assert_array_equal(a['final'][field],b['final'][field])
            self.assertEqual(a['stats']['steps'],b['stats']['steps'])

    def test_independent_reference_annulus_conservation(self):
        from model import Config,Inputs
        from p2_reference import IndependentBDF2
        s=IndependentBDF2(Config(n=40),Inputs())
        old=1+s.x**2
        new=s.solve(old,old,np.full(40,1e-8),np.ones(41),.02,0.,0.,(1/30,-1/30,0))
        self.assertLess(abs(float(s.dv@(new-old))),1e-13)
        same=s.solve(np.full(41,.7),np.full(41,.7),np.full(40,1e-8),
                     np.ones(41),.02,8e-7,.7,(1/30,-1/30,0))
        np.testing.assert_allclose(same,.7,rtol=1e-13)

    def test_independent_reference_real_inputs(self):
        from model import Solver,Config,Inputs
        from p2_reference import IndependentBDF2
        for moving in (False,True):
            cfg=Config(material=4 if moving else 3,shrink=moving,n=160,
                       max_time=120,stop_dry=False,output_stride=1)
            a=Solver(cfg).run();b=IndependentBDF2(cfg,Inputs()).run()
            np.testing.assert_allclose(a['final']['T'],b['final']['T'],rtol=0,atol=1e-6)
            np.testing.assert_allclose(a['final']['C'],b['final']['C'],rtol=0,atol=1e-9)

    def test_sampling_does_not_change_valid_trajectory(self):
        from model import Solver,Config
        args=dict(material=1,n=10,early_dt=.5,max_time=60,stop_dry=False)
        a=Solver(Config(**args,keep_short=False)).run()
        b=Solver(Config(**args,keep_short=True)).run()
        np.testing.assert_array_equal(a['final']['C'],b['final']['C'])
        self.assertEqual(a['stats']['steps'],b['stats']['steps'])

    def test_cache_provenance_covers_input_bytes(self):
        import tempfile
        from pathlib import Path
        from run_study import provenance
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'input';p.write_bytes(b'first')
            a=provenance([p]);p.write_bytes(b'second');b=provenance([p])
            self.assertNotEqual(a,b)

if __name__=='__main__': unittest.main()

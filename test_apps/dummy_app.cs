using System;
using System.Threading;

public class DummyApp
{
    public static void Main(string[] args)
    {
        Console.WriteLine($"DummyApp ({AppDomain.CurrentDomain.FriendlyName}) started."); // Display process name for clarity
        if (args.Length > 0 && args[0].ToLower() == "/continuous")
        {
            Console.WriteLine("DummyApp running in continuous mode...");
            int counter = 0;
            try
            {
                while (true)
                {
                    Console.WriteLine($"{DateTime.Now} - DummyApp ({AppDomain.CurrentDomain.FriendlyName}) continuous mode heartbeat: {counter++}");
                    Thread.Sleep(5000); // 5 seconds
                }
            }
            catch (ThreadInterruptedException)
            {
                Console.WriteLine("DummyApp continuous mode interrupted. Exiting.");
            }
        }
        else if (args.Length > 0 && args[0].ToLower() == "/error")
        {
            Console.WriteLine("DummyApp simulating an error exit.");
            Environment.Exit(1); // Exit with error code 1
        }
        else
        {
            Console.WriteLine($"DummyApp ({AppDomain.CurrentDomain.FriendlyName}) finished normally.");
            Environment.Exit(0); // Ensure explicit exit code 0
        }
    }
}
